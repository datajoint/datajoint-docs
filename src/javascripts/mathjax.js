window.MathJax = {
  tex: {
    inlineMath: [["$", "$"], ["\\(", "\\)"]],
    displayMath: [["$$", "$$"], ["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: "no-mathjax",
    processHtmlClass: "arithmatex|jp-RenderedHTMLCommon|jp-RenderedMarkdown"
  },
  startup: {
    ready: () => {
      MathJax.startup.defaultReady();
    }
  }
};
