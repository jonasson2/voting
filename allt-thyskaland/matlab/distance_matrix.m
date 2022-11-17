function D = distance_matrix(lond)
  centers = {
    'Baden-Württemberg', 48,32,16, 9,2,28
    'Bayern', 48,56,47, 11,24,15
    'Berlin', 52,30,10.4, 13,24,15.1
    'Brandenburg', 52,28,0, 13,23,0
    'Bremen', 53,19,0, 8,43,0
    'Hamburg', 53,34,8, 10,1,44
    'Hessen', 50,36,29, 9,1,42
    'Mecklenburg-Vorpommern', 53,46,24.6, 12,34,32
    'Niedersachsen', 52,50,23.4, 9,4,33.7
    'Nordrhein-Westfalen', 51,28,42, 7,33,18
    'Rheinland-Pfalz', 49,57,18.5, 7,18,37.5
    'Saarland', 49,23,3, 6,57,13
    'Sachsen', 50,55,46.1, 13,27,30
    'Sachsen-Anhalt', 52,0,32.6, 11,42,9.6
    'Schleswig-Holstein', 54,11,8, 9,49,20
    'Thüringen', 50,54,12, 11,1,35
    };
  function dd = dms2degrees(dms)
    dd = dms(:,1) + dms(:,2)/60 + dms(:,3)/3600;
  end
  function D = distance(lat1, lon1, lat2, lon2)
    R = 6371;
    dlam = lon2 - lon1;
    D = R*acos(sind(lat1)*sind(lat2) + cosd(lat1)*cosd(lat2)*cosd(dlam));
  end
  N = zeros(1,16);
  E = zeros(1,16);
  for i=1:length(centers)
    land = string(centers(i,1));
    k = find(lond==land);
    N(k) = dms2degrees(cell2mat(centers(i,2:4)));
    E(k) = dms2degrees(cell2mat(centers(i,5:7)));
  end
  D = zeros(16,16);
  for i=1:16
    for j=1:i-1
      D(i,j) = distance(N(i),E(i),N(j),E(j));
    end
  end
  D = D + D';
end