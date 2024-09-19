# twitter thread on which we are building the MVP ( LOL )

- This is a readme generated by ai for an AI agent who tracks topics of interest for you
  It analyses all postive data for your topic
  It analyses all negative data for your topic
  It checks for data factually
  It creates a summary of the topic
  It creates a positive sumamry
  
- Rest is left to the user the app doesnt provide conclusions only data from all forms and validations

```bash 
Nishant Singh
@iNishant
·
4h
Feel free to copy this good/bad idea. DM if you want to build this together.

LLM-driven news timeline generator. I want to stay updated on all events related to certain issues. While this is almost search engine territory, might be a fun experiment to build from scratch.
Neel Seth
@NeelSeth7
10$/month  ? Mein deta raat tak. News tracker agent, track your own keywords latest news ?
2:17 PM · Jul 20, 2024
·
63
 Views
View post engagements
Related posts

Nishant Singh
@iNishant
·
3h
De dunga 😆, bana tu

P0 requirements
- Basic timeline UI with timestamps, summaries
- Each summary with sources

Sample input "Puja Khedkar controversy"
```

## P0 product and user journey

- user signs up with email
- user lands on plan selection page
  - the user can opt for free plan
    - free plan has no limitations of number of analysis but they can also add only 10 keywords to track
    - the user needs to provide their own anthropic and tavily api keys
  - the user can opt for paid plan
    - the paid plan user can add only 10 keywords and run analysis 20 times a day in total or twice per keyword for that matter
    - the paid user does not provide any keys, we use the keys stored in our env variables as we are charging the user
- user post selecting the plan lands on keyword additon page
  - here the user can add maximum 10 keywords for all kind of plans
  - user can come back to the page and delete a keyword add new but total keywords added should not cross 10
- Once keywords are added the user can go the feed page where the list of keywords is visible in tiles waiting to run the first analysis
  - the user clicks on run analysis
  - we run ai based background simulation to run analysis
  - we keep updating the analysis status in a table to be tracked
  - once analysis is completed we update the analysis status as well the data for the keyword
- the user can click on any keyword tile on the feed page to see details
  - the detailss page has a sumamry, positive content, negative cotent sources of all content and fact checked sources
- Users can signup and login add keywords etc without selecting any plan also, however if the user is not a paid plan user or a free plan user ( as to start free plan api keys are needed ) the start analysis button will prompt the user to select any one of the plan

## Technology stack

- Tavily API for search
- Anthropic LLM for ai
- Flask python backend
- Jinja 2 templates - tailwind css
- Supabase with email password
- Heroku for hosting
- Supabase database 
- Rabitmq connection to manage long running and background task

### Folder Structure

```bash
news_app/
    backend/ # flask
        app/
            templates/
                base.html # base template with basic layout
                components/
                    header.html # header component
                    footer.html # footer component
                onboarding/
                    keyword.html # News keyword selection / removal page
                    plans.html # User plan selection page
                auth/
                    login.html # Login page, login with supabase - server side
                    signup.html # Signup page with supabase - server side
                main/
                    feed.html # News Feed
                    news.html # News detail page
            routes/
                __init__.py # empty routes file
                auth.py # authentication routes
                main.py # all other rotues
            models/ # this has only services for models as tables are directly created on supabase
                __init__.py # empty init file
                data_service.py # data services to work with supabase database
            services/
                prompts/
                    promptfile.txt # prompt for ai
                tools/
                    search.json # tools available for ai agent
                    positive.json # tools available for ai agent
                    negative.json # tools available for ai agent
                    summary.json # tools available for ai agent
                __init__.py # services init file empty
                agent.py # main agent service with recusrive ai simulation
                ai.py # additional ai tool
                context.py # ai analysis context builder for simulation
                search.py # search service
                supabase_auth.py # supabase auth services create user / update etc
            utils/
                __init__.py # empty init file
                redis_task_manager.py # empty file need to work on this
            static/
                css/ #empty folder
                js/ # empty
            __init__.py
            env # local env file for local testing loaded using python dotenv
            config.py # config of the app
            extensions.py # app extensions
            supabase_config.py # supabase client setup
            redis_config.py # redis connection setup
        myvenv/ # local virtual environment
        requirements.txt 
        Procfile # heroku gunicorn run file
        run.py # local flask run file
        run_worker.py # running redis worker
    readme.md
```


### Supabase tables

