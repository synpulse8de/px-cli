#!/usr/bin/env node

import {spawn} from "child_process";
import path from "path";
import {fileURLToPath} from "url";
import readline from "readline";
import chalk from "chalk";
import {readFileSync, writeFileSync} from "fs";

global.dirName = undefined;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
});

export async function updateProject(projectName) {
    await customPostCreationActions();
}

async function getCurrentVersions() {
        const filePath = global.dirName + '/package.json'; // Replace with the path to your JSON file
        const rawData = readFileSync(filePath, 'utf-8');
        const jsonData = JSON.parse(rawData);

        const a = jsonData.dependencies.next;
        const b = jsonData.dependencies.react;
        const c = jsonData.dependencies.react-dom;

        console.log(a)
        console.log(b)
        console.log(c)
}

async function customPostCreationActions() {
    // await promptAPI()
    //     .then(/*adding api logic goes here*/)
    //     .catch((error) => {
    //         console.error('Error:', error);
    //     })
    //
    // await promptKeyCloak()
    //     .then(/*adding keycloak logic goes here!*/)
    //     .catch((error) => {
    //         console.error('Error:', error);
    //     })


    await getCurrentVersions()

    installPackage('pnpm', ['up', 'next', 'react', 'react-dom', 'eslint-config-next', '--latest']).then(() => {


        console.log(chalk.green('Project successfully upgraded to Version') + ' was copied to destination');
        console.log(chalk.blue('Please visit \u2192 https://nextjs.org/docs/pages/building-your-application/upgrading '));
        console.log(chalk.blue('to see '));
    }).catch((err) => {
        console.log("ERROR", err)
    })
    // rl.resume()*/
}

function installPackage(pkgMgr, args) {
    return new Promise((resolve) => {
        const installProcess = spawn(pkgMgr, args, {
            stdio: 'inherit',
            cwd: global.dirName,
        });

        installProcess.on('close', (code) => {
            if (code === 0) {
                resolve(code);
            } else {
                console.error('Error while installing' + args[1]);
            }
        });
    })
}

function promptForName() {
    return new Promise((resolve) => {
        rl.question('Please enter project name: ', (name) => {
            if (!name) {
                console.log('Name cannot be empty. Please try again.');
                promptForName().then(resolve); // Call the function recursively to prompt again
            } else {
                resolve(name);
            }
            rl.pause();
        });
    });
}

/*
async function promptAPI() {
    return await enquirer.prompt({
        type: 'select',
        name: 'apiSelect',
        message: 'Choose an API technology',
        choices: ['REST', 'GraphQl', 'gRPC']
    });
}

async function promptKeyCloak() {
    return await enquirer.prompt({
        type: 'toggle',
        name: 'keyCloakToggle',
        message: 'Do you need keycloack integration?',
        initial: false,
    });
}

*/

updateProject()
