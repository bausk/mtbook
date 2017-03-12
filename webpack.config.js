'use strict';

var path = require('path');

// Dev or Prod
var NODE_ENV = process.env.NODE_ENV || 'development';
require('babel-polyfill');

var common = require( path.resolve( __dirname, "./common.config.js" ) );

common.devtool = 'inline-source-map';
common.output =  {
        path: ('../main/static/js'),
        filename: 'app.js'
    };

common.watch = NODE_ENV == 'development';
common.watchOptions = { aggregateTimeout: 100};

module.exports = common;
