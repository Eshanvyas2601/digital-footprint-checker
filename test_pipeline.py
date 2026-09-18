from serpapi_client import search_text, build_targeted_query
from analyzer import analyze_results

query = build_targeted_query("Eshan Vyas", "name")
results = search_text(query)
report = analyze_results(results, "name", "Eshan Vyas")
print(report)