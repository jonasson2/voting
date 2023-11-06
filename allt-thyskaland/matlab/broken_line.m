function b = broken_line(bp, val)
  % Broken line with breakpoints [0, bp(1),... ] with values val(1), val(2),...
  % ending as constant to the right of bp(end)
  bp(end+1) = bp(end) + 1;
  val(end+1) = val(end);
  b = griddedInterpolant(bp, val);
end