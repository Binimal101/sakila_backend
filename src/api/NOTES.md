
*Overall Tech Stack Learned*

pydantic models can take input directly from ORM data (if we pull from sqlalchemy) or by dict/json (fastapi DI)

*FastAPI*

Learned about routers (how you can attach multiple routers to a single app to stratify your codebase / app)
Learned about dependency injection (using to get fresh db instances on each req, and to validate addrs)

*Pydantic*

Learned about how to create pydantic models with BaseModel, decided for project to create models for 
HTTP input and what we can expect to output from any given endpoint

learned how to tie together ORM objects into model instantiation

learned about constraints and fields (computed field was cool)

*SQLAlchemy*

Learned how to create models using Column() and add on fk, index, and other constraints using \_\_table\_args\_\_