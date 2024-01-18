import requests
import json
from bs4 import BeautifulSoup
from queue import Queue
from threading import Thread
import os


class Worker(Thread):

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                print(e)
            finally:
                self.tasks.task_done()


class ThreadPool:

    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        """Add a list of tasks to the queue"""
        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()


class RecipeWriter:
    def __init__(self, sample_size=10):
        self.file_name = "recipes.json"
        self.file = open(self.file_name, "w+")
        if len(self.file.read()) > 0:
            print("File exists, overwriting...")
            self.file.write("[]")

        self.file.seek(0)
        self.queue = Queue()
        self.sample_size = sample_size
        self.writes = 0
        self.complete = False
        self.errors = []

    def add_to_queue(self, data):
        self.queue.put(data)

    def write_to_file(self):
        try:
            self.writes += 1
            self.file.seek(0)
            file_data = self.file.read()
            if len(file_data) > 0:
                json_data = json.loads(file_data)
            else:
                json_data = []
            if not self.queue.empty():
                data = self.queue.get()
                json_data.append(data)
                self.file.seek(0)
                self.file.write(json.dumps(json_data))
                self.file.truncate()
                os.system("cls")
                print("WRITE |", data["name"])
                print("REMAINING |", self.writes, "/", self.sample_size)
                print("WRITE ERRORS |", self.errors)
        except Exception as e:
            self.errors.append(("Write to file", e))

    def wait_completion(self):
        self.complete = True

    def run(self):
        try:
            while not self.complete or not self.queue.empty():
                if not self.queue.empty():
                    self.write_to_file()
                    self.queue.task_done()
        except Exception as e:
            self.errors.append(e)


class Recipes:
    def __init__(self, sample_size=10):
        self.sample_size = sample_size
        self.write = RecipeWriter(sample_size=self.sample_size)
        self.write_thread = Thread(target=self.write.run)

        self.recipe_url_pool = []
        self.pool = ThreadPool(10)
        self.req = requests.Session()
        self.errors = []

    def fetch_recipes(self):
        url = f"https://www.bbcgoodfood.com/api/recipes-frontend/search/recommended-items?&limit={self.sample_size}&clientId=1&postType=recipe&category=recipes"
        response = requests.get(url)
        data = response.json()

        for item in data["items"]:
            self.recipe_url_pool.append(item.get("url", ""))

        self.write_thread.start()
        self.pool.map(self.fetch_recipe, self.recipe_url_pool)
        self.pool.wait_completion()
        self.write.wait_completion()
        self.write_thread.join()

        print("Done")
        print("FETCH ERRORS:", self.errors)

    def fetch_recipe(self, url):
        try:
            print("FETCH |", url)
            if url == "":
                return
            url = "https://www.bbcgoodfood.com" + url
            recipe_body = requests.get(url)
            soup = BeautifulSoup(recipe_body.text, "html.parser")
            data = soup.find("script", id="__NEXT_DATA__")
            data = json.loads(data.text)
            recipe = data["props"]["pageProps"]

            rawIngredients = recipe["ingredients"][0]["ingredients"]
            allIngredients = []
            # Ingredients
            for ingredient in rawIngredients:
                ingredients = {
                    "text": ingredient["ingredientText"],
                }
                if ingredient.get("note"):
                    ingredients["note"] = ingredient["note"]
                if ingredient.get("quantityText"):
                    ingredients["quantity"] = ingredient["quantityText"]
                allIngredients.append(ingredients)

            # Nutritional Info
            nutritionalInfo = recipe.get("nutritionalInfo", [])
            nutritionalInfoF = None

            for nutrition in nutritionalInfo:
                label = nutrition.get("label")
                value = nutrition.get("value")
                prefix, suffix = nutrition.get("prefix"), nutrition.get("suffix")
                nutritionalInfoF = {
                    "label": label,
                    "value": value,
                    "prefix": prefix,
                    "suffix": suffix,
                }
            # Skill level and time
            skillLevel = recipe.get("skillLevel")
            cookPrepTime = recipe.get("cookAndPrepTime", {})
            prepTime = cookPrepTime.get("preparationMax")
            cookTime = cookPrepTime.get("cookingMax")
            totalTime = cookPrepTime.get("total")
            image = recipe.get("image", {}).get(
                "url",
                "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/1665px-No-Image-Placeholder.svg.png",
            )

            # Method
            methodSteps = recipe.get("methodSteps", [])
            servings = recipe.get("servings")
            # remove any alpha characters from servings
            numServings = ""
            numFound = False
            try:
                for i in range(len(servings) - 1, 0, -1):
                    if servings[i].isdigit():
                        numFound = True
                        numServings = servings[i] + numServings
                    elif numFound:
                        break
            except Exception as e:
                numServings = None
                self.errors.append((url, e))
            try:
                numServings = int(numServings)
            except ValueError:
                numServings = None
                print("Error converting servings to int")

            methodF = []
            stepNum = 0
            for step in methodSteps:
                stepNum += 1
                if step.get("type") == "step":
                    content = step.get("content")
                    for c in content:
                        if c.get("type") == "html":
                            instructionHtml = c.get("data", {}).get("value")
                            instructionSoup = BeautifulSoup(
                                instructionHtml, "html.parser"
                            )
                            instructionF = instructionSoup.get_text()
                            methodF.append(
                                {"step": stepNum, "instruction": instructionF}
                            )
            recipeData = {
                "name": recipe["title"],
                "nutrition": nutritionalInfoF,
                "skillLevel": skillLevel,
                "servings": servings,
                "numServings": numServings,
                "image": image,
                "cookPrepTime": {
                    "prepTime": prepTime,
                    "cookTime": cookTime,
                    "totalTime": totalTime,
                },
                "methodSteps": methodF,
                "ingredients": allIngredients,
            }
            self.write.add_to_queue(recipeData)

        except Exception as e:
            self.error.append((url, e))
            return


a = Recipes(sample_size=10)
a.fetch_recipes()
