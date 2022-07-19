const appPresets = ['@vue/babel-preset-app', "@babel/preset-typescript"];
const libPresets = ['@babel/preset-env', "@babel/preset-typescript"];
module.exports = {
  presets: (process.title === 'webpack' ? appPresets : libPresets),
};
