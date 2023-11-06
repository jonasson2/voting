function large_marker_legend(strings, colors, msiz, location)
  if ~exist('location', 'Var')
    location = 'northwest';
  end
  n = length(strings);
  for i=1:n
    p(i) = plot(nan, nan, '.', color=colors(i,:), markersize=msiz*1.5);
  end
  leg = legend(p, strings{:}, location=location);
end