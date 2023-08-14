#!/usr/bin/env node

import {spawn} from "child_process";
import chalk from "chalk";
import enquirer from "enquirer";
import {copyFile, mkdir, readFileSync, writeFileSync} from "fs";
import path from "path";
import {fileURLToPath} from "url";
import readline from "readline";

global.dirName = undefined;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
});

export async function createNextJsFE(projectName) {
    if (!projectName) {
        projectName = await promptForName();
    } else {
        rl.pause();
    }

    const options = ['create-next-app', projectName, '--use-pnpm', '--ts', '--eslint', '--app', '--src-dir', '--tailwind', '--import-alias','@/*'];
    const childProcess = spawn('npx', options, {stdio: 'inherit'});

    childProcess.on('close', async (code) => {
        if (code === 0) {
            console.log('\u2192 ' + chalk.green('Next.js project created successfully!'));
            global.dirName = process.cwd() + '/' + projectName;
            console.log('\u2192 Set global installation directory to' + global.dirName + 'for further installations');
            await copyFiles(projectName).then(() => {
                console.log('\u2192 ' + chalk.yellow('lint-staged.config.js') + ' was copied to destination');
                console.log('\u2192 ' + chalk.yellow('.prettierrc.json') + ' was copied to destination');
            })

            await customPostCreationActions();

            const basicStructureFolders = ['pages', 'components', 'utils', 'hooks', 'shared']
            await addAndRemoveFilesFromNewProject(projectName, basicStructureFolders);
        } else {
            console.error('Error creating Next.js project');
        }
    });
}

async function customPostCreationActions() {
    await promptAPI()
        .then(/*adding api logic goes here*/)
        .catch((error) => {
            console.error('Error:', error);
        })

    await promptKeyCloak()
        .then(/*adding keycloak logic goes here!*/)
        .catch((error) => {
            console.error('Error:', error);
        })

    installPackage('pnpm', ['i', '@typescript-eslint/eslint-plugin']).then(() => {
        installPackage('pnpm', ['i', 'prettier', '--save-dev']).then(() => {
            installPackage('pnpm', ['i', 'eslint-config-prettier', '--save-dev']).then(() => {
                installPackage('pnpm', ['i', 'husky', '--save-dev']).then(() => {
                    installPackage('pnpm', ['husky', 'install']).then(() => {
                        installPackage('pnpm', ['husky', 'add', '.husky/pre-commit', 'pnpm lint-staged']).then(() => {
                            installPackage('pnpm', ['i', 'lint-staged', '--save-dev']).then(() => {
                                editTsConfig(dirName)
                            })
                        })
                    })
                })
            })
        })
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

function editTsConfig() {

    const filePath = global.dirName + '/tsconfig.json'; // Replace with the path to your JSON file
    const rawData = readFileSync(filePath, 'utf-8');
    const jsonData = JSON.parse(rawData);

    jsonData.compilerOptions.moduleResolution = 'node'; // Change the 'moduleResolution' property to 'node'

    const updatedData = JSON.stringify(jsonData, null, 2); // Convert JavaScript object to JSON string with 2-space indentation
    writeFileSync(filePath, updatedData, 'utf-8');

    console.log('\u2192 ', chalk.green('JSON file updated successfully!'));
}

async function copyFiles(projectName) {
    const lintStageSrc = path.resolve(__dirname, '../..', 'resources', 'lint-staged.config.js');
    try {
        copyFile(lintStageSrc, projectName + '/lint-staged.config.js', (err) => {
            if (err) throw err;
        });
    } catch (e) {
        console.log("Something went wrong while copying lint-staged.config.js to destination", e)
        return Promise.reject(e)
    }

    const prettierSrc = path.resolve(__dirname, '../..', 'resources', '.prettierrc.json');
    try {
        copyFile(prettierSrc, projectName + '/.prettierrc.json', (err) => {
            if (err) throw err;
        });
    } catch (e) {
        console.log("Something went wrong while copying .prettierrc.json to destination", e)
        return Promise.reject(e)
    }
    return Promise.resolve();
}

async function addAndRemoveFilesFromNewProject(projectName, basicStructureFolders) {
    basicStructureFolders.map((folderName) => {
        try {
            mkdir(path.join(projectName, 'src', 'app', folderName), (err) => {
                if (err) {
                    return console.error(err);
                }
            });
        } catch (e) {
            console.log('Directory ' + folderName + ' couldn\'t be created');
            return Promise.reject(e)
        }
    })

    console.log('\u2192 ', chalk.green('Directories created successfully!'));
    return Promise.resolve();
}
