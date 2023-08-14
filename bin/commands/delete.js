#!/usr/bin/env node

import enquirer from 'enquirer';
import {fileURLToPath} from "url";
import path from "path";
import { resolve } from 'path';
import { rmdirSync } from 'fs';

const base = process.env.PWD

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export async function initDelete(pathToDelete) {
    if (pathToDelete) {
        console.log(`Deleting project at path: ${pathToDelete}`);
        // Perform the deletion logic here using the provided path.
    } else {

        const response = await enquirer.prompt({
            type: 'input',
            name: 'path',
            message: 'Enter the path of the project to delete:',
        });

        console.log(response, __dirname, base)
        const inputPath = response.path.trim();

        if (inputPath === '') {
            console.log('No path provided. Aborting deletion.');
            return;
        }

        const resolvedPath = resolve(inputPath);
        console.log(resolvedPath)
        if (resolvedPath === __dirname) {
            console.log('Deleting current directory.');
            // rmdirSync(resolvedPath, { recursive: true });
        } else {
            console.log(`Deleting project at path: ${resolvedPath}`);
            // Perform the deletion logic here using the resolved path.
        }
        // Perform the deletion logic here using the provided path.
    }
}
