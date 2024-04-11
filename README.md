# Installation

1. Clone the repository:
   ```
   git clone https://github.com/charanravi-online/tenderfix
   ```
2. navigate into the task/task/solution/ folder
   ```
   cd /task/task/solution/
   ```
4. Run the docker-compose file to get everything set up.
   ```
   docker-compose build
   docker-compose up
   ```
   The server should be up and running.
5. data from the excel files are pushed into the database and data.db will be created.
6. task-2.csv will be created automatically.
7. The csv file 1 can be generated when we hit the endpoint /entries/ with the belegnummer
   ```
   http://localhost:8000/entries/12100024
   ```
8. the localhost route should be accessible where the entire database is exposed (for debugging purpose)
   ```
   database: http://localhost:8000/database/
   ```

## Note
There were time contraints which didn't allow me to work on this project fully.
But I did get to learn a few things.
