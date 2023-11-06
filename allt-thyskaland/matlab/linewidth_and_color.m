function [lw, clr] = linewidth_and_color(varargin)
  [top, linewidth] = getKeywordParams(top=true, linewidth=4);
  if top
    lw = linewidth; 
    clr = [rgb("dodgerblue"), 0.6]; 
  else
    lw = linewidth; 
    clr = "darkgray"; 
  end
end

