const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

let completionItems = [];
let watcher = null;

/**
 * Scan .tex files and build completion list
 */
function scanNotes(rootPath) {
    const items = [];
    const dirs = ['notes', 'articles', 'wiki'];

    for (const dir of dirs) {
        const dirPath = path.join(rootPath, dir);
        if (!fs.existsSync(dirPath)) continue;

        const files = fs.readdirSync(dirPath)
            .filter(f => f.endsWith('.tex'))
            .map(f => {
                const fullPath = path.join(dirPath, f);
                const stat = fs.statSync(fullPath);
                const name = path.basename(f, '.tex');
                const title = extractTitle(fullPath) || name;

                return {
                    name,
                    title,
                    path: `${dir}/${f}`,
                    mtime: stat.mtimeMs
                };
            });

        items.push(...files);
    }

    // Sort by modification time (most recent first)
    items.sort((a, b) => b.mtime - a.mtime);

    return items;
}

/**
 * Extract title from .tex file
 */
function extractTitle(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf8');

        // Try \Title{...}
        let match = content.match(/\\Title\{([^}]+)\}/);
        if (match) return match[1];

        // Try \title{...}
        match = content.match(/\\title\{([^}]+)\}/);
        if (match) return match[1];

        // Try \GWikiMeta{...}{title}{...}
        match = content.match(/\\GWikiMeta\{[^}]*\}\{([^}]+)\}/);
        if (match) return match[1];

    } catch (e) {
        // Ignore errors
    }
    return null;
}

/**
 * Build VS Code completion items
 */
function buildCompletionItems(notes) {
    return notes.map((note, index) => {
        const item = new vscode.CompletionItem(
            note.title,
            vscode.CompletionItemKind.Reference
        );

        // Insert just the name (filename)
        item.insertText = note.name;

        // Show path in detail
        item.detail = note.path;

        // Sort by recency
        item.sortText = String(index).padStart(4, '0');

        // Documentation
        item.documentation = new vscode.MarkdownString(
            `**${note.title}**\n\n` +
            `File: \`${note.path}\`\n\n` +
            `Insert: \`\\wref{${note.name}}\``
        );

        return item;
    });
}

/**
 * Refresh completions
 */
function refreshCompletions() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) return;

    const rootPath = workspaceFolders[0].uri.fsPath;
    const notes = scanNotes(rootPath);
    completionItems = buildCompletionItems(notes);

    console.log(`GWiki: Loaded ${completionItems.length} completions`);
}

/**
 * Activate extension
 */
function activate(context) {
    console.log('GWiki Autocomplete activated');

    // Initial scan
    refreshCompletions();

    // Register completion provider
    const provider = vscode.languages.registerCompletionItemProvider(
        ['latex', 'tex'],
        {
            provideCompletionItems(document, position) {
                // Get text before cursor
                const linePrefix = document.lineAt(position).text.substr(0, position.character);

                // Check if we're inside \wref{...}
                const wrefMatch = linePrefix.match(/\\wref\{([^}]*)$/);
                if (!wrefMatch) {
                    return undefined;
                }

                const partial = wrefMatch[1].toLowerCase();

                // Filter completions by partial match
                let filtered = completionItems;
                if (partial) {
                    filtered = completionItems.filter(item => {
                        const label = item.label.toLowerCase();
                        const insert = item.insertText.toLowerCase();
                        return label.includes(partial) || insert.includes(partial);
                    });
                }

                return filtered;
            }
        },
        '{' // Trigger on opening brace
    );

    // Register refresh command
    const refreshCommand = vscode.commands.registerCommand(
        'gwiki.refreshCompletions',
        () => {
            refreshCompletions();
            vscode.window.showInformationMessage(
                `GWiki: Refreshed ${completionItems.length} completions`
            );
        }
    );

    // Register new note command
    const newNoteCommand = vscode.commands.registerCommand(
        'gwiki.newNote',
        async () => {
            const name = await vscode.window.showInputBox({
                prompt: 'Note filename (without .tex)',
                placeHolder: 'my-new-note'
            });

            if (!name) return;

            const title = await vscode.window.showInputBox({
                prompt: 'Note title',
                placeHolder: 'My New Note'
            });

            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders) return;

            const rootPath = workspaceFolders[0].uri.fsPath;
            const notesDir = path.join(rootPath, 'notes');

            // Create notes directory if it doesn't exist
            if (!fs.existsSync(notesDir)) {
                fs.mkdirSync(notesDir, { recursive: true });
            }

            const filePath = path.join(notesDir, `${name}.tex`);

            const content = `\\documentclass{gwiki}

\\Title{${title || name}}
\\Tags{}

\\begin{document}

\\NoteHeader

%% Your content here...

\\end{document}
`;

            fs.writeFileSync(filePath, content);

            // Open the new file
            const doc = await vscode.workspace.openTextDocument(filePath);
            await vscode.window.showTextDocument(doc);

            // Refresh completions
            refreshCompletions();
        }
    );

    // Watch for file changes
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders) {
        const rootPath = workspaceFolders[0].uri.fsPath;

        watcher = vscode.workspace.createFileSystemWatcher(
            new vscode.RelativePattern(rootPath, '{notes,articles,wiki}/*.tex')
        );

        watcher.onDidCreate(() => refreshCompletions());
        watcher.onDidDelete(() => refreshCompletions());
        watcher.onDidChange(() => refreshCompletions());

        context.subscriptions.push(watcher);
    }

    context.subscriptions.push(provider, refreshCommand, newNoteCommand);
}

/**
 * Deactivate extension
 */
function deactivate() {
    if (watcher) {
        watcher.dispose();
    }
}

module.exports = { activate, deactivate };
