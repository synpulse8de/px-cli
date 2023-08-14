#!/usr/bin/env node

import {hideBin} from 'yargs/helpers'
import _yargs from 'yargs';
import {createNextJsFE} from "./commands/create.js";
import {initDelete} from "./commands/delete.js";
import {updateProject} from "./commands/update.js";

const yargs = _yargs(hideBin(process.argv));

async function init() {
    await yargs
        .command('frontend', 'Create a new frontend', (x) => {
            yargs
                .command(['create', 'c'], 'Create a new frontend', async () => {
                    const projectName = x.argv._[2];
                    if (projectName) {
                        await createNextJsFE(projectName);
                    } else {
                        await createNextJsFE();
                    }
                })
                .command(['update', 'u'], 'Update an existing frontend', () => {
                    console.log('Updating frontend...', x.argv._[2]);
                    // updateFrontend();
                    updateProject()
                })
                .command(['add', 'a'], 'Add package to frontend', () => {
                    console.log('Deleting frontend...', x.argv._[2]);
                    // deleteFrontend();
                })
                .demandCommand(1, 'You must specify a subcommand');
        })
        .command(['delete', 'd'], 'Delete a project', () => {
            console.log('Deleting frontend...');
            // deleteFrontend();
            initDelete()
        })
        .demandCommand(1, 'You must specify a command')
        .help()
        .parse();
}

init()
