'use strict'
const { VueLoaderPlugin } = require('vue-loader')
var path = require('path');
module.exports = {
  mode: 'development',
  entry: [
    './src/app.js'
  ],
  output: {
    library: 'voting',
    libraryTarget: 'umd',
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'static/js/')
  },
  resolve: {
    alias: {
      vue: '@vue/compat'
    }
  },
  module: {
    rules: [
      {
        test: /\.vue$/,
        loader: 'vue-loader',
        options: {
          compilerOptions: {
            compatConfig: { MODE: 2 }
          }
        }
      },
      {
        test: /\.css$/,
        use: [
          'style-loader',
          {
            loader: 'css-loader',
            options: { esModule: false }
          },
        ]
      }
    ]
  },
  plugins: [
    new VueLoaderPlugin()
  ]
}
