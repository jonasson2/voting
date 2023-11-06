function broken_line_plot(b, varargin)
  [TOP, LW] = getKeywordParams(top = true, linewidth = 4);
  [lw, clr] = linewidth_and_color(linewidth=LW);
  x = b.GridVectors{1};
  xmax = max(x);
  t = linspace(0, xmax);
  bt = b(t);
  ph = plot(t, bt, color=clr, linewidth=lw);
  if ~TOP
    uistack(ph, 'bottom')
  end
end
