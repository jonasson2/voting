%#ok<*AGROW> 
function [pv, cv, flokkar, lond, litir, ar] = read_votes()
  json = jsondecode(fileread('../partyvotes.json'));
  ar = json.years;
  flokkar = json.parties;
  nparty = length(flokkar);
  lond = json.lander;
  flokkar = string(flokkar);
  litir = {}; 
  for l=json.colors'
    litir{end+1} = rgb(l{1});
  end
  litir = cell2mat(litir');
  nland = length(lond);
  pv = permute(json.pv, [1,3,2]);
  for p = 1:nparty
    for l = 1:nland
      cvpl = json.cvote_dict{p}{l};
      cv{p}{l} = [];
      fields = fieldnames(cvpl);
      for k = 1:length(fields)
        field = fields{k};
        cv{p}{l}(:,end+1) = cvpl.(field);
      end
    end
  end
end
