const syntaxHighlight = require("@11ty/eleventy-plugin-syntaxhighlight");
const markdownIt = require("markdown-it");
const markdownItTaskLists = require("markdown-it-task-lists");
const markdownItCallouts = require("markdown-it-obsidian-callouts");

module.exports = function (eleventyConfig) {
  eleventyConfig.addPlugin(syntaxHighlight);

  const md = markdownIt({ html: true, linkify: true, typographer: true })
    .use(markdownItTaskLists)
    .use(markdownItCallouts);
  eleventyConfig.setLibrary("md", md);

  eleventyConfig.addPassthroughCopy("css");

  eleventyConfig.addWatchTarget("_includes/");
  eleventyConfig.addWatchTarget("css/");

  return {
    dir: { input: ".", output: "_site", includes: "_includes", data: "_data" },
    markdownTemplateEngine: "njk",
    pathPrefix: process.env.ELEVENTY_PATH_PREFIX || "/",
  };
};
