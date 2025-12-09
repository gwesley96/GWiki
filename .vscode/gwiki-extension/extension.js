const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

let completionItems = [];
let watcher = null;

/**
 * Normalize a string for loose matching (ignores case and separators).
 */
const normalize = (value = '') =>
    value
        .toLowerCase()
        .replace(/[\s_\-–—()]/g, '')
        .replace(/[^a-z0-9]/g, '');

const ensureList = (value) => {
    if (!value) return [];
    if (Array.isArray(value)) return value.map((v) => `${v}`.trim()).filter(Boolean);
    return `${value}`
        .split(',')
        .map((v) => v.trim())
        .filter(Boolean);
};

const parseFrontmatter = (content) => {
    const pattern = /^\s*%?\s*---\s*\n([\s\S]*?)\n\s*%?\s*---/m;
    const match = content.match(pattern);
    if (!match) return {};

    const block = match[1]
        .split('\n')
        .map((line) => line.replace(/^\s*%+\s?/, ''));

    const data = {};
    let currentKey = null;

    for (const raw of block) {
        const line = raw.trim();
        if (!line) continue;

        if (line.includes(':') && !line.startsWith('-')) {
            const [keyPart, ...rest] = line.split(':');
            const key = keyPart.trim().toLowerCase().replace(/\s+/g, '_');
            const value = rest.join(':').trim();

            if (value) {
                if (value.startsWith('[') && value.endsWith(']')) {
                    data[key] = value
                        .slice(1, -1)
                        .split(',')
                        .map((v) => v.trim())
                        .filter(Boolean);
                } else {
                    data[key] = value;
                }
            } else {
                data[key] = [];
            }
            currentKey = key;
            continue;
        }

        if (line.startsWith('-') && currentKey) {
            data[currentKey] = data[currentKey] || [];
            if (Array.isArray(data[currentKey])) {
                const item = line.replace(/^-/, '').trim();
                if (item) data[currentKey].push(item);
            }
        }
    }

    return data;
};

const extractNoteMetadata = (fullPath, relativeDir, stat) => {
    const name = path.basename(fullPath, '.tex');
    let title = null;
    let tags = [];
    let aliases = [];

    try {
        const content = fs.readFileSync(fullPath, 'utf8');

        const frontmatter = parseFrontmatter(content);
        if (frontmatter) {
            title = frontmatter.title || title;
            tags = ensureList(frontmatter.tags || frontmatter.tag) || tags;
            aliases = ensureList(frontmatter.aliases || frontmatter.alias) || aliases;
        }

        const metaMatch = content.match(/\\GWikiMeta\{[^}]*\}\{([^}]+)\}\{[^}]+\}(?:\[([^\]]*)\])?(?:\[([^\]]*)\])?/);
        if (metaMatch) {
            title = title || metaMatch[1];
            if (!tags.length && metaMatch[2]) {
                tags = ensureList(metaMatch[2]);
            }
            if (!aliases.length && metaMatch[3]) {
                aliases = ensureList(metaMatch[3]);
            }
        }

        if (!title) {
            const titleMatch =
                content.match(/\\Title\{([^}]+)\}/) ||
                content.match(/\\title\{([^}]+)\}/);
            if (titleMatch) title = titleMatch[1];
        }

        if (!tags.length) {
            const tagMatch = content.match(/\\Tags\{([^}]+)\}/);
            if (tagMatch) tags = ensureList(tagMatch[1]);
        }

        if (!aliases.length) {
            const aliasMatch = content.match(/\\Aliases\{([^}]+)\}/);
            if (aliasMatch) aliases = ensureList(aliasMatch[1]);
        }
    } catch (e) {
        // Ignore and fall back to filename-based metadata
    }

    return {
        name,
        title: title || name,
        path: `${relativeDir}/${path.basename(fullPath)}`,
        mtime: stat.mtimeMs,
        tags,
        aliases,
    };
};

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
                return extractNoteMetadata(fullPath, dir, stat);
            });

        items.push(...files);
    }

    // Sort by modification time (most recent first)
    items.sort((a, b) => b.mtime - a.mtime);

    return items;
}

/**
 * Build VS Code completion items
 */
function buildCompletionItems(notes) {
    const items = [];

    notes.forEach((note, index) => {
        const base = new vscode.CompletionItem(
            note.title,
            vscode.CompletionItemKind.Reference
        );

        base.insertText = note.name;
        base.detail = note.path;
        base.sortText = String(index).padStart(4, '0');
        base.filterText = [
            note.name,
            note.title,
            ...note.aliases,
            normalize(note.name),
            normalize(note.title),
            ...note.aliases.map((a) => normalize(a)),
        ].filter(Boolean).join(' ');
        base.documentation = new vscode.MarkdownString(
            `**${note.title}**\n\n` +
            `File: \`${note.path}\`\n\n` +
            `Insert: \`\\wref{${note.name}}\`` +
            (note.aliases.length ? `\n\nAliases: ${note.aliases.join(', ')}` : '')
        );

        items.push(base);

        note.aliases.forEach((alias, aliasIndex) => {
            const aliasItem = new vscode.CompletionItem(
                alias,
                vscode.CompletionItemKind.Reference
            );
            aliasItem.insertText = new vscode.SnippetString(
                `${note.name}[${alias}]`
            );
            aliasItem.detail = `${note.title} • alias`;
            aliasItem.sortText = `${String(index).padStart(4, '0')}-a${String(aliasIndex).padStart(2, '0')}`;
            aliasItem.filterText = [
                alias,
                note.name,
                normalize(alias),
                normalize(note.name),
                normalize(note.title),
            ].filter(Boolean).join(' ');
            aliasItem.documentation = new vscode.MarkdownString(
                `**${alias}** → ${note.title}\n\n` +
                `File: \`${note.path}\`\n\n` +
                `Insert: \`\\wref{${note.name}}[${alias}]\``
            );
            items.push(aliasItem);
        });
    });

    return items;
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

                const partial = wrefMatch[1] || '';
                const replaceRange = new vscode.Range(
                    position.translate(0, -partial.length),
                    position
                );
                const safeText = (value) => {
                    if (!value) return '';
                    if (typeof value === 'string') return value;
                    if (typeof value.value === 'string') return value.value;
                    return '';
                };

                // Filter completions by partial match
                let filtered = completionItems;
                if (partial) {
                    const normalizedPartial = normalize(partial);
                    filtered = completionItems.filter(item => {
                        const label = safeText(item.label).toLowerCase();
                        const insert = safeText(item.insertText).toLowerCase();
                        if (label.includes(partial.toLowerCase()) || insert.includes(partial.toLowerCase())) {
                            return true;
                        }
                        // Allow matching when user types with dashes/spaces
                        const normalizedLabel = normalize(label);
                        const normalizedInsert = normalize(insert);
                        return normalizedLabel.includes(normalizedPartial) ||
                               normalizedInsert.includes(normalizedPartial);
                    });
                }

                return filtered.map((item) => {
                    item.range = replaceRange;
                    return item;
                });
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
