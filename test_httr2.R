library(httr2)

resp <- request("https://api.github.com/users/octocat") |>
  req_headers(Accept = "application/json") |>
  req_perform()

print(resp_status(resp))
print(resp_body_json(resp))
