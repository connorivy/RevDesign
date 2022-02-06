// https://betterprogramming.pub/vue-django-using-vue-files-and-the-vue-cli-d6dd8c9145eb
// this is the tutorial for implenting vue into django. Refer back for production instructions

const path = require('path');

module.exports = {
    publicPath: '/static/src/vue/dist/', // Should be STATIC_URL + path/to/build
    outputDir: path.resolve(__dirname, '../static/src/vue/dist/'), // Output to a directory in STATICFILES_DIRS
    filenameHashing: false, // Django will hash file names, not webpack
    runtimeCompiler: true, // See: https://vuejs.org/v2/guide/installation.html#Runtime-Compiler-vs-Runtime-only
    devServer: {
        writeToDisk: true, // Write files to disk in dev mode, so Django can serve the assets
    },
    transpileDependencies: ['vuetify', '@speckle/viewer']
};


// module.exports = {
//   configureWebpack: {
//     devtool: 'source-map'
//   },
//   productionSourceMap: false,
//   pages: {
//     app: {
//       entry: 'src/main/app.js',
//       title: 'Speckle',
//       template: 'public/app.html',
//       filename: 'app.html'
//     },
//     embedApp: {
//       entry: 'src/embed/embedApp.js',
//       title: 'Speckle Embed Viewer',
//       template: 'public/embedApp.html',
//       filename: 'embedApp.html'
//     }
//   },
//   devServer: {
//     host: 'localhost',
//     proxy: 'http://localhost:3000',
//     historyApiFallback: {
//       rewrites: [
//         { from: /^\/$/, to: '/app.html' },
//         { from: /./, to: '/app.html' }
//       ]
//     }
//   },
//   transpileDependencies: ['vuetify', '@speckle/viewer']
// }
