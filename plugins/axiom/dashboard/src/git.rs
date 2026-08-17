use std::path::{Path, PathBuf};
use std::process::Command;

use crate::model::{GitFile, GitState};

pub fn inspect_repo(repo_hint: Option<&Path>) -> GitState {
    let start = repo_hint
        .map(PathBuf::from)
        .or_else(|| std::env::current_dir().ok())
        .unwrap_or_else(|| PathBuf::from("."));

    let root_output = Command::new("git")
        .arg("-C")
        .arg(&start)
        .args(["rev-parse", "--show-toplevel"])
        .output();

    let root_output = match root_output {
        Ok(output) if output.status.success() => output,
        Ok(output) => {
            return GitState {
                error: Some(clean_stderr(&output.stderr, "not a Git repository")),
                ..GitState::default()
            }
        }
        Err(error) => {
            return GitState {
                error: Some(format!("git is unavailable: {error}")),
                ..GitState::default()
            }
        }
    };

    let root = String::from_utf8_lossy(&root_output.stdout).trim().to_owned();
    let branch = run_git(&root, &["branch", "--show-current"])
        .ok()
        .map(|value| value.trim().to_owned())
        .filter(|value| !value.is_empty())
        .or_else(|| {
            run_git(&root, &["rev-parse", "--short", "HEAD"])
                .ok()
                .map(|value| format!("detached@{}", value.trim()))
        });

    let status = match run_git(&root, &["status", "--porcelain=v1", "-z"] ) {
        Ok(value) => value,
        Err(error) => {
            return GitState {
                available: true,
                root: Some(root),
                branch,
                error: Some(error),
                ..GitState::default()
            }
        }
    };

    let mut files = Vec::new();
    let mut staged = 0usize;
    let mut unstaged = 0usize;
    let mut untracked = 0usize;
    let entries: Vec<&str> = status.split('\0').filter(|entry| !entry.is_empty()).collect();
    let mut index = 0usize;
    while index < entries.len() {
        let entry = entries[index];
        if entry.len() < 3 {
            index += 1;
            continue;
        }
        let x = entry.chars().next().unwrap_or(' ');
        let y = entry.chars().nth(1).unwrap_or(' ');
        let mut path = entry[3..].to_owned();
        if (x == 'R' || x == 'C') && index + 1 < entries.len() {
            path = format!("{} → {}", entries[index + 1], path);
            index += 1;
        }
        if x == '?' && y == '?' {
            untracked += 1;
        } else {
            if x != ' ' && x != '?' {
                staged += 1;
            }
            if y != ' ' && y != '?' {
                unstaged += 1;
            }
        }
        files.push(GitFile {
            path,
            index_status: x.to_string(),
            worktree_status: y.to_string(),
        });
        index += 1;
    }

    let mut insertions = 0u64;
    let mut deletions = 0u64;
    if let Ok(numstat) = run_git(&root, &["diff", "HEAD", "--numstat", "--"] ) {
        for line in numstat.lines() {
            let mut parts = line.split('\t');
            if let Some(value) = parts.next() {
                insertions = insertions.saturating_add(value.parse::<u64>().unwrap_or(0));
            }
            if let Some(value) = parts.next() {
                deletions = deletions.saturating_add(value.parse::<u64>().unwrap_or(0));
            }
        }
    }

    GitState {
        available: true,
        root: Some(root),
        branch,
        changed_files: files.len(),
        staged_files: staged,
        unstaged_files: unstaged,
        untracked_files: untracked,
        insertions,
        deletions,
        files,
        error: None,
    }
}

fn run_git(root: &str, args: &[&str]) -> Result<String, String> {
    let output = Command::new("git")
        .arg("-C")
        .arg(root)
        .args(args)
        .output()
        .map_err(|error| format!("failed to run git: {error}"))?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).into_owned())
    } else {
        Err(clean_stderr(&output.stderr, "git command failed"))
    }
}

fn clean_stderr(stderr: &[u8], fallback: &str) -> String {
    let value = String::from_utf8_lossy(stderr).trim().to_owned();
    if value.is_empty() {
        fallback.to_owned()
    } else {
        value
    }
}
