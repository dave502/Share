const console = require("console");
const express = require("express");
const app = express();
const server = require("http").Server(app);
const cors = require('cors');

const io = require("socket.io")(server, {
  cors: {
    origin: "*",
  },
  path: "/server/"
});

const redis = require("redis");


const main = async () => {

  let orders = new Map();


  //Creating a redis client
  const redisClientPub = redis.createClient({
    url: process.env.REDIS_URL
    });
  redisClientPub.on('error', (err) => console.log('Redis Client Error', err));

  (async () => {
    // Connect to redis server
    await redisClientPub.connect();
  })();

  console.log("Attempting to connect to redis...");
  redisClientPub.on('connect', () => {
      console.log('Connected!');
  });


  // creating a redis subscriber
    const redisClientSub = redisClientPub.duplicate();
    await redisClientSub.connect();

    app.get("/", (req, res) => {
      res.send(`success ${typeof(redisClientPub)==="object"}`);
    });

    app.get("/server", (req, res) => {
      res.send(`server ${typeof(redisClientPub)==="object"}`);
    });

    app.get("/history-data/:ticker/",  cors(), async(req, res) => {

      const ticker = req.params.ticker
      const start = req.query.start
      const end = req.query.end

      const prices = await redisClientPub.ts.mRangeWithLabels(start?start:"-", end?end:"+", `agg_prices=True`)
      const orders = await redisClientPub.ts.mRangeWithLabels(start?start:"-", end?end:"+", `agg_orders=True`)

      ticker_prices = prices.filter(function (el) {
        return  el.labels.share === ticker;
      });

      ticker_orders = orders.filter(function (el) {
        return  el.labels.share === ticker;
      });

      if (ticker_prices[0].samples.length){
        console.log("samples", ticker_prices[0].samples, ticker_prices[0].samples===true, ticker_prices[0].samples==true)

        ticker_prices = ticker_prices[0].samples.map(({timestamp:timems, value: value})=>({time:timems, price: value}));

        ticker_orders.forEach(function(obj) {
          let name = obj.labels.name;
          if (name === "buys"){
            obj.samples = obj.samples.map(({timestamp:timems, value: value})=>({time:timems, buys: value}));
          } else if (name === "sells") {
            obj.samples = obj.samples.map(({timestamp:timems, value: value})=>({time:timems, sells: value}));
          }
        });

        const mergeByTime = (arr1, arr2, arr3) =>
          arr1.map(itm1 => ({
              ...arr2.find((item) => (item.time === itm1.time) && item),
              ...arr3.find((item) => (item.time === itm1.time) && item),
              ...itm1
        }));

        data = mergeByTime(ticker_prices, ticker_orders[0].samples, ticker_orders[1].samples)
        res.send({ data: data});
      } else {
        res.send({});
      }
    });

    app.get("/shares-data",  cors(), async(req, res) => {
      await redisClientPub.hGetAll('shares')
      .then(data => {res.send(data)})
      .catch(err => console.log(err));
    });


    await redisClientSub.subscribe("orders_and_prices", (message) => {

      dict = JSON.parse(message)
      Object.keys(dict).forEach(key => {
        if (orders.has(key)){
          if (orders.get(key).at(-1).time === dict[key].time){
            orders.get(key)[orders.get(key).length - 1] = dict[key]
          }
          else{
            orders.set(key, [...orders.get(key), dict[key]].slice(-10))
          }
        }
        else {orders.set(key, [dict[key]])};
        io.emit(key, { channel: "CHANNEL", message: JSON.stringify(orders.get(key))});
      });
    });

    // Creating a websocket connection.
    io.on("connection", (socket) => { 
      console.log('Got connection!');
        socket.on("subscribe", async (channel) => {
          console.log('Subscribed!');
      });

      socket.on("unsubscribe", async (channel) => {
        await redisClientSub.unsubscribe(channel);
      });

      socket.on("send message", async (channel, message) => {
        await redisClientPub.publish(channel, message);
      });
    });

  server.listen(8000, () => {
    console.log("Server is running");
  });
};

main();
