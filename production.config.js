'use strict';

var path = require('path');
require('babel-polyfill');
var webpack = require('webpack');


var common = require( path.resolve( __dirname, "./common.config.js" ) );

common.plugins.push(new webpack.DefinePlugin({
      'process.env':{
        'NODE_ENV': JSON.stringify('production')
      }
    }));

common.output =  {
        path: ('../build/static/js'),
        filename: 'app.js'
    };

module.exports = common;