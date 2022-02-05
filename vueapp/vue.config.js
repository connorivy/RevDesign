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
};