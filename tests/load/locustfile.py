from locust import HttpUser, task, between


class OpenBMCUser(HttpUser):
    host = "https://localhost:2443"
    wait_time = between(1, 3)

    @task
    def get_system(self):
        with self.client.get(
            "/redfish/v1/Systems/system",
            auth=("root", "0penBmc"),
            verify=False,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()

                if "PowerState" in data:
                    response.success()
                else:
                    response.failure("PowerState отсутствует в ответе")
            else:
                response.failure(f"HTTP {response.status_code}")

class PublicAPIUser(HttpUser):
    host = "https://jsonplaceholder.typicode.com"
    wait_time = between(1, 3)

    @task
    def get_posts(self):
        self.client.get("/posts")

    @task
    def get_weather(self):
        self.client.get(
            "https://wttr.in/Novosibirsk?format=j1",
            name="/Novosibirsk?format=j1"
        )