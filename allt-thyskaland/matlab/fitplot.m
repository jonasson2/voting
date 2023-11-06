function fitplot(x,y)
  X = linspace(min(x), max(x));
  p = polyfit(x, y, 1);
  Y = polyval(p, X);
  plot(X, Y, linewidth=4, color=rgb('lightgray'))
  hold on
  scatter(x, y, 10, rgb('darkblue'), "filled", 'o')
  hold off
end