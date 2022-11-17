function [pv, cv, flokkar, lond, litir, ar] = read_votes()
  json = jsondecode(fileread('../partyvotes.json'));
  nparty = size(json.pv, 1);
  flokkar = json.parties;
  lond = json.lander;
  flokkar = string(flokkar);
  litir = {}; 
  for l=json.colors'
    litir{end+1} = rgb(l{1});
  end
  litir = cell2mat(litir');
  ar = json.years;
  nland = length(lond);
  pv = permute(json.pv, [3,1,2]);
  for p = 1:nparty
    for l = 1:nland
      cv{p}{l} = json.cv{p}{l}';
    end
  end
end
