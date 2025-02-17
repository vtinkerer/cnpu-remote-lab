# CPNU Remote Lab (Buck and Boost converter)

Repository for both back-end and front-end parts of CPNU Remote Lab web application for conducting Buck and Boost converter experiments.

## Features

1. Performing Buck converter experiment.
2. Performing Boost converter experiment.
3. Switches, round sliders, buttons as control elements.
4. Visualizing oscilloscope (Current, Voltage and PWM values).
5. Voltage vs PWM graph.
6. Saving graphs as PNG-files.

## Used technologies

TypeScript, Vue.js, Bootstrap, HTML, CSS, JavaScript, Docker, Node.js, Python.

## How to run web application (locally)

1. Clone the repository.
2. Install all libraries by running `npm ci` command in root folder.
3. Create .env file and init all necessary global variables (including setting `is_fake_user_session` to `true`).
4. Run back-end in root folder by `npm run backend` command.
5. Run front-end in root folder by `npm run frontend:build:watch` command.
6. Deploy web application locally in root folder by `docker-compose -f "docker-compose.yml" up -d --build` command.
7. Go to http://localhost:80?session_id=1234567890 and enjoy the application!

## How to run web application (globally)
1. Go to the http://rlms.stu.cn.ua:8080/lde/.
2. Enter given credentials.
3. Choose `Buck converter` or `Boost converter` laboratory.
4. Conduct the experiments!