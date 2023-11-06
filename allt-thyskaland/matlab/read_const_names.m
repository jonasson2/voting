%#ok<*AGROW> 
function constituency_names = read_const_names()
  json = jsondecode(fileread('../partyvotes.json'));
  constituency_names = json.const;
end
