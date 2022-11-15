function [west, east] = landdist()
  function D = dist_matrix(cells)
    D = zeros(length(cells));
    for i = 1:length(cells)
      D(i, 1:length(cells{i})) = cells{i};
    end
    D = D + D';
  end
  west = {
    []
    [1]
    [1,1]
    [2,2,1]
    [2,2,1,2]
    [2,2,1,2,1]
    [3,3,2,3,1,1]
    [3,3,2,3,2,1,1]
    [3,3,2,3,2,1,2,1]
    [4,4,3,4,2,2,1,2,3]
    };
  east = {
    []
    [1]
    [2,1]
    [3,2,1]
    [2,1,1,1]
    };
  west = dist_matrix(west);
  east = dist_matrix(east);
end
