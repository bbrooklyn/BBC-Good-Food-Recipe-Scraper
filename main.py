import json
database = "recipes.json"
data = json.loads(open(database).read())
temprecipelist = []
endresults = []
UserKCAL_Pday = 2300
UserKCAL_Pmeal = UserKCAL_Pday/3
#User Inputs

PreferredCookTime = int(input("Enter the preferred cook time: (Minutes): \n"))
TimeOfDay = input("Enter the time of day for these meals? (Breakfast, Lunch, Dinner): \n").lower()
PreferredServings = int(input("Enter the preferred servings: \n"))
NumberOfMeals =  int(input("Enter the number of meals you are searching for: \n"))

#Extra Inputs for calorie preference
if input("Would you like to add a suggested calories? (Y,N) \n") != "N":
  Gender = input("Enter your gender (Male, Female): \n")
  Age = int(input("Enter your age \n"))
  Weight = float(input("Enter your weight: (KG) \n"))
  Height = float(input("Enter your height: (Ft) \n"))
  print(""" 1. Little or no exercise)
          2.Light Exercise (1-3 days)
          3.Moderately Active (3-5 days)
          4.Very Active (6-7)
          5.Extra Active (Constant) """)

  Activity = input("Enter your weekly exercise: (1,2,3,4,5) ")



#Algrotihms
  BMR = {
    "male": (13.397*Weight)+(4.799*(Height*30.48))-(5.677*Age)+88.362,
    "female": (9.25*Weight)+(3.1*(Height*30.48))-(4.33*Age) + 447.6
  }

  EXVAL = {
    '1':1.2,
    '2':1.375,
    '3':1.55,
    '4':1.725,
    '5':1.9
  }

  UserKCAL_Pday = BMR[Gender] *EXVAL[Activity]
  UserKCAL_Pmeal = UserKCAL_Pday/3



# Open the JSON file
with open("recipes.json") as f:
  # Load the JSON data
  data = json.load(f)

# Get all values of name
for recipe in data:
    if recipe["numServings"] == PreferredServings and (TimeOfDay in (recipe["recipeCategory"])[0].lower()):
        temprecipelist.append(recipe)

for recipe in temprecipelist: #bigger process so better done on smaller data set
  if (recipe["cookPrepTime"]["cookTime"])//60 > PreferredCookTime and (recipe["nutrition"][0])["value"] >  UserKCAL_Pmeal*1.2:
    temprecipelist.remove(recipe)


#Sample has been fetched relatign to requirments, it will not have the algorithm applied to it


for recipe in temprecipelist:
    
    CaloriesPercent = (((recipe["nutrition"][0])["value"])/UserKCAL_Pday)*100
    endresults.append([recipe,CaloriesPercent])
    endresults.sort(reverse = True, key = lambda x: x[1])

for i in range(len(endresults)):
    if i >= NumberOfMeals:
      break

    print((endresults[i])[0]["name"])

