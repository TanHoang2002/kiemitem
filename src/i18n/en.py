"""English string catalog — keys equal their values for transparent fallback."""

STRINGS_EN: dict[str, str] = {
    # ── Settings window ────────────────────────────────────────────────────
    "Settings": "Settings",
    "Save": "Save",
    "Cancel": "Cancel",
    "OK": "OK",
    "Yes": "Yes",
    "No": "No",
    "Restart now": "Restart now",
    "Later": "Later",
    "Reset Settings": "Reset Settings",
    "Would you like to reset only the '{tab_name}' settings or all settings to defaults?": (
        "Would you like to reset only the '{tab_name}' settings or all settings to defaults?"
    ),
    "Reset {tab_name}": "Reset {tab_name}",
    "Reset All Tabs": "Reset All Tabs",
    "This will reset ALL custom values in your params.ini. Are you sure?": (
        "This will reset ALL custom values in your params.ini. Are you sure?"
    ),
    "Reset to defaults": "Reset to defaults",
    "Restart required": "Restart required",
    "Vision mode changes require restarting d4lf. Restart now?": (
        "Vision mode changes require restarting d4lf. Restart now?"
    ),
    "Restart failed": "Restart failed",
    "d4lf could not be restarted automatically. Please restart it manually.": (
        "d4lf could not be restarted automatically. Please restart it manually."
    ),
    "Error validating value": "Error validating value",
    "Your value has been reset to its previous version.": (
        "Your value has been reset to its previous version."
    ),
    "Set Hotkey": "Set Hotkey",
    "Press the key or combination of keys you\nwant to use as a hotkey, then click save.": (
        "Press the key or combination of keys you\nwant to use as a hotkey, then click save."
    ),
    "Search settings...": "Search settings...",
    "Key Bindings": "Key Bindings",
    "Technical Settings": "Technical Settings",
    # ── Settings category labels (SettingsCategory enum values) ────────────
    "📦 Loot Behavior": "📦 Loot Behavior",
    "📄 Profiles": "📄 Profiles",
    "🤖 Automation": "🤖 Automation",
    "🎒 Stash & Transfer": "🎒 Stash & Transfer",
    "🎨 UI & Theme": "🎨 UI & Theme",
    "⚙️ System & Paths": "⚙️ System & Paths",
    "⌨️ Hotkeys": "⌨️ Hotkeys",
    "🛠️ Advanced": "🛠️ Advanced",
    # ── MoveItemsType labels in tab_mixin ──────────────────────────────────
    "Favorites": "Favorites",
    "Junk": "Junk",
    "Unmarked": "Unmarked",
    # ── Dashboard ──────────────────────────────────────────────────────────
    "Dashboard": "Dashboard",
    "Full Logs": "Full Logs",
    "ACTIVE PROFILES": "ACTIVE PROFILES",
    "Toggle profiles to enable them. Drag <b>⠿</b> to set priority; the top profile determines affix highlighting.": (
        "Toggle profiles to enable them. Drag <b>⠿</b> to set priority; the top profile determines affix highlighting."
    ),
    "Filter profiles...": "Filter profiles...",
    "Enable All": "Enable All",
    "Disable All": "Disable All",
    "KEYBOARD SHORTCUTS": "KEYBOARD SHORTCUTS",
    "Show Activity Log": "Show Activity Log",
    "Import Profile": "Import Profile",
    "Settings": "Settings",
    "Minimize to Tray": "Minimize to Tray",
    "Vision Mode: STOPPED": "Vision Mode: STOPPED",
    "Vision Mode: RUNNING": "Vision Mode: RUNNING",
    "Vision Mode: Disabled (GUI-only)": "Vision Mode: Disabled (GUI-only)",
    "TTS: Disconnected": "TTS: Disconnected",
    "TTS: Connected": "TTS: Connected",
    "TTS: Disabled (GUI-only)": "TTS: Disabled (GUI-only)",
    "TTS connection has not been made yet. Have you followed all of the instructions in %s? If so, it's possible your Windows user does not have the correct permissions to allow Diablo 4 to connect to a third party screen reader.": (
        "TTS connection has not been made yet. Have you followed all of the instructions in %s? "
        "If so, it's possible your Windows user does not have the correct permissions to allow Diablo 4 "
        "to connect to a third party screen reader."
    ),
    # ── Profile card ───────────────────────────────────────────────────────
    "Edit": "Edit",
    "Edit Profile": "Edit Profile",
    "Delete": "Delete",
    "Delete Profile": "Delete Profile",
    "Are you sure you want to permanently delete the profile '{name}'?": (
        "Are you sure you want to permanently delete the profile '{name}'?"
    ),
    "No Profiles found. Please import a profile below.": (
        "No Profiles found. Please import a profile below."
    ),
    "Last Modified:": "Last Modified:",
    "Items:": "Items:",
    "Affix Filters:": "Affix Filters:",
    "Aspect Upgrades:": "Aspect Upgrades:",
    "Global Uniques:": "Global Uniques:",
    "Sigils: Included": "Sigils: Included",
    "Tributes: Included": "Tributes: Included",
    "Paragon Overlay: Data Found": "Paragon Overlay: Data Found",
    "(Could not parse profile details)": "(Could not parse profile details)",
    # ── Tray ───────────────────────────────────────────────────────────────
    "Restore": "Restore",
    "Exit": "Exit",
    "D4 Loot Filter": "D4 Loot Filter",
    "D4LF settings reload failed": "D4LF settings reload failed",
    "D4LF profile loading": "D4LF profile loading",
    # ── Profile editor ─────────────────────────────────────────────────────
    "Profile Editor": "Profile Editor",
    "Profile": "Profile",
    "Undo Changes": "Undo Changes",
    "Instructions": "Instructions",
    "Select a profile from the dropdown. Click 'Save' to save your changes. Click 'Undo Changes' to revert your changes.": (
        "Select a profile from the dropdown. Click 'Save' to save your changes. Click 'Undo Changes' to revert your changes."
    ),
    "Unsaved Changes": "Unsaved Changes",
    "You have unsaved changes. Do you want to save them before closing?": (
        "You have unsaved changes. Do you want to save them before closing?"
    ),
    "Alert": "Alert",
    "--------- Active Profiles ---------": "--------- Active Profiles ---------",
    "--------- Inactive Profiles ---------": "--------- Inactive Profiles ---------",
    "No profiles found": "No profiles found",
    "Profile Validation Failed": "Profile Validation Failed",
    "Validation Error": "Validation Error",
    "Info": "Info",
    "Profile saved successfully": "Profile saved successfully",
    "Profile saved successfully to {name}": "Profile saved successfully to {name}",
    "Warning": "Warning",
    "The profile model might not be valid. Do you still want to save your changes ?": (
        "The profile model might not be valid. Do you still want to save your changes ?"
    ),
    "Profile not saved.": "Profile not saved.",
    "Error": "Error",
    "Remove Selected": "Remove Selected",
    "Select at least one rule to remove.": "Select at least one rule to remove.",
    "Add": "Add",
    "Remove": "Remove",
    "Delete Items": "Delete Items",
    "Items": "Items",
    "Select items to delete:": "Select items to delete:",
    "Set Min Power": "Set Min Power",
    "Min Power:": "Min Power:",
    "Set Min Greater Affix": "Set Min Greater Affix",
    "Min Greater Affix:": "Min Greater Affix:",
    "Set Min Percent Of Affix": "Set Min Percent Of Affix",
    "Min Percent Of Affix:": "Min Percent Of Affix:",
    # ── Profile editor per-section tabs ────────────────────────────────────
    "Affixes": "Affixes",
    "Value": "Value",
    "Min %": "Min %",
    "Unique Aspects": "Unique Aspects",
    "Create Item": "Create Item",
    "Remove Item": "Remove Item",
    "Set All Min GAs (Excludes Auto Synced Items)": "Set All Min GAs (Excludes Auto Synced Items)",
    "Convert All To Min %": "Convert All To Min %",
    "Set all minPower": "Set all minPower",
    "Item name already exist please rename {item_name} in the profile file.": (
        "Item name already exist please rename {item_name} in the profile file."
    ),
    "Aspect Upgrades": "Aspect Upgrades",
    "Add any legendary aspects you'd like to have favorited if an upgrade is found. See the readme on AspectUpgrades for more information.": (
        "Add any legendary aspects you'd like to have favorited if an upgrade is found. See the readme on AspectUpgrades for more information."
    ),
    "Add Aspect": "Add Aspect",
    "Sigils": "Sigils",
    "Add Sigil": "Add Sigil",
    "Remove Whitelist Sigil": "Remove Whitelist Sigil",
    "Remove Blacklist Sigil": "Remove Blacklist Sigil",
    "Priority:": "Priority:",
    "Rarities:": "Rarities:",
    "Blacklist": "Blacklist",
    "Whitelist": "Whitelist",
    "Sigil already exist in whitelist. You can modify the existing one.": (
        "Sigil already exist in whitelist. You can modify the existing one."
    ),
    "Sigil already exist in blacklist. You can modify the existing one.": (
        "Sigil already exist in blacklist. You can modify the existing one."
    ),
    "Add tribute names and select rarities you want to keep. Leaving rarities empty keeps all rarities.": (
        "Add tribute names and select rarities you want to keep. Leaving rarities empty keeps all rarities."
    ),
    "Add Tribute": "Add Tribute",
    "Rarities:": "Rarities:",
    "Select at least one tribute rule to remove.": "Select at least one tribute rule to remove.",
    "Global Unique Rule": "Global Unique Rule",
    "Profile Alias:": "Profile Alias:",
    "Minimum Power:": "Minimum Power:",
    "Min Greater Affixes:": "Min Greater Affixes:",
    "Min Percent of Aspect:": "Min Percent of Aspect:",
    "Create Rule": "Create Rule",
    "Remove Rule": "Remove Rule",
    "Unique Rule {index}": "Unique Rule {index}",
    "Create {kind}": "Create {kind}",
    "Remove {kind}": "Remove {kind}",
    "{kind} name already exists, please rename {item_name} in the profile file.": (
        "{kind} name already exists, please rename {item_name} in the profile file."
    ),
    "No sets selected": "No sets selected",
    "Auto Sync": "Auto Sync",
    "When checked: Min Greater Affixes automatically matches the number of affixes marked as 'want greater'\nWhen unchecked: You can manually set Min Greater Affixes to any value": (
        "When checked: Min Greater Affixes automatically matches the number of affixes marked as 'want greater'\n"
        "When unchecked: You can manually set Min Greater Affixes to any value"
    ),
    "Default file name: {value}": "Default file name: {value}",
    "Custom file name:": "Custom file name:",
    "Leave blank for default filename": "Leave blank for default filename",
    "Default filename includes...": "Default filename includes...",
    "Found {count} variants in {source}.\nSelect which variants to keep:": (
        "Found {count} variants in {source}.\nSelect which variants to keep:"
    ),
    "Variant {index}": "Variant {index}",
    "Import Aspect Upgrades": "Import Aspect Upgrades",
    "If legendary aspects are in the build, do you want an aspect upgrades section generated for them?": (
        "If legendary aspects are in the build, do you want an aspect upgrades section generated for them?"
    ),
    "Import Charms": "Import Charms",
    "If a build has charms, should they be included in the imported profile?": (
        "If a build has charms, should they be included in the imported profile?"
    ),
    "Import Seals": "Import Seals",
    "If a build has seals, should they be included in the imported profile?": (
        "If a build has seals, should they be included in the imported profile?"
    ),
    "Add to profiles": "Add to profiles",
    "Do you want to add this build to your active profiles upon generating?": (
        "Do you want to add this build to your active profiles upon generating?"
    ),
    "Include GAs": "Include GAs",
    "Include the greater affix tags from the build, making it look for GAs?": (
        "Include the greater affix tags from the build, making it look for GAs?"
    ),
    "Require all GAs": "Require all GAs",
    "Are the GAs required to match the item?": "Are the GAs required to match the item?",
    "Import Paragon": "Import Paragon",
    "Import paragon boards for the paragon overlay?": "Import paragon boards for the paragon overlay?",
    "Multi Build Import": "Multi Build Import",
    "Import multiple builds from the link?": "Import multiple builds from the link?",
    "You can link either the build guide or a direct link to the specific planner.\n\nhttps://maxroll.gg/d4/build-guides/tornado-druid-guide\nor\nhttps://maxroll.gg/d4/planner/cm6pf0xa#5\nor\nhttps://d4builds.gg/builds/ef414fbd-81cd-49d1-9c8d-4938b278e2ee\nor\nhttps://mobalytics.gg/diablo-4/builds/barbarian/bash\nor\nhttps://infinitybuilds.gg/en/builds/barbarian-fL8P6vVSqI\n\nIt will create a file based on the label of the build in the planner in: {user_dir}\\profiles\n\n": (
        "You can link either the build guide or a direct link to the specific planner.\n\n"
        "https://maxroll.gg/d4/build-guides/tornado-druid-guide\n"
        "or\n"
        "https://maxroll.gg/d4/planner/cm6pf0xa#5\n"
        "or\n"
        "https://d4builds.gg/builds/ef414fbd-81cd-49d1-9c8d-4938b278e2ee\n"
        "or\n"
        "https://mobalytics.gg/diablo-4/builds/barbarian/bash\n"
        "or\n"
        "https://infinitybuilds.gg/en/builds/barbarian-fL8P6vVSqI\n\n"
        "It will create a file based on the label of the build in the planner in: {user_dir}\\profiles\n\n"
    ),
    "Source": "Source",
    "Season": "Season",
    "Class": "Class",
    "Build title": "Build title",
    "Select at least one filename part or enter a custom file name.": (
        "Select at least one filename part or enter a custom file name."
    ),
    "none": "none",
    # ── Importer wizard ────────────────────────────────────────────────────
    "Profile Importer - d2core / Maxroll / D4Builds / Mobalytics / InfinityBuilds": (
        "Profile Importer - d2core / Maxroll / D4Builds / Mobalytics / InfinityBuilds"
    ),
    "Log:": "Log:",
    "Instructions:": "Instructions:",
    "URL:": "URL:",
    "Generate": "Generate",
    "Generating...": "Generating...",
    "Saving...": "Saving...",
    "Enter a URL to generate a profile.": "Enter a URL to generate a profile.",
    "Select variants to import": "Select variants to import",
    # ── Overlay (info panel) ───────────────────────────────────────────────
    "World Boss:": "World Boss:",
    "Legion:": "Legion:",
    "Helltide:": "Helltide:",
    "GPH:": "GPH:",
    "Pending": "Pending",
    "|Gained:": "|Gained:",
    "Gained:": "Gained:",
    "EPH:": "EPH:",
    "|Exp:": "|Exp:",
    "Exp:": "Exp:",
    "T2L:": "T2L:",
    "|Next Scan:": "|Next Scan:",
    "Next Scan:": "Next Scan:",
    "Ready": "Ready",
    "SETTINGS": "SETTINGS",
    "Track Gold": "Track Gold",
    "Show Gold Per Hour": "Show Gold Per Hour",
    "Show Gold Gained": "Show Gold Gained",
    "Gold Config": "Gold Config",
    "Track Exp": "Track Exp",
    "Show EXP Per Hour": "Show EXP Per Hour",
    "Show EXP Gained": "Show EXP Gained",
    "Show Time to Level": "Show Time to Level",
    "Show Next Scan": "Show Next Scan",
    "Auto-Capture Exp When Inventory Opened": "Auto-Capture Exp When Inventory Opened",
    "EXP Capture Time": "EXP Capture Time",
    "Configure EXP Bar Position": "Configure EXP Bar Position",
    "Reset EXP Bar Position": "Reset EXP Bar Position",
    "Exp Config": "Exp Config",
    "Reset Gold": "Reset Gold",
    "Reset Exp": "Reset Exp",
    "Reset Stats": "Reset Stats",
    "Orientation:": "Orientation:",
    "Increase Size (+)": "Increase Size (+)",
    "Decrease Size (-)": "Decrease Size (-)",
    "Font": "Font",
    "Never": "Never",
    "0m": "0m",
    "3m": "3m",
    "5m": "5m",
    "10m": "10m",
    "30m": "30m",
    "60m": "60m",
    "Refresh Timers Now": "Refresh Timers Now",
    "Lock Position": "Lock Position",
    "Close Overlay": "Close Overlay",
    "DRAG ACROSS YOUR EXPERIENCE BAR\n(Escape to cancel)": (
        "DRAG ACROSS YOUR EXPERIENCE BAR\n(Escape to cancel)"
    ),
    # ── LOGGER.info user-facing messages (handler.py, loot/, etc.) ─────────
    "Reloaded hotkeys from updated settings": "Reloaded hotkeys from updated settings",
    "Reloaded language assets for %s": "Reloaded language assets for %s",
    "Please restart d4lf manually to apply %s.": "Please restart d4lf manually to apply %s.",
    "Closing Paragon overlay": "Closing Paragon overlay",
    "Opening Paragon overlay (source: %s)": "Opening Paragon overlay (source: %s)",
    "Closing Info Panel overlay": "Closing Info Panel overlay",
    "Opening Info Panel overlay": "Opening Info Panel overlay",
    "Stopping filter or move process": "Stopping filter or move process",
    "Running loot filter": "Running loot filter",
    "Loot filter done": "Loot filter done",
    "Mark as favorite": "Mark as favorite",
    # ── Bridge confirm UI ──────────────────────────────────────────────────
    "(no preview)": "(no preview)",
    "(no image)": "(no image)",
    "Parsed item (editable before send):": "Parsed item (editable before send):",
    "Account:": "Account:",
    "Send": "Send",
    "Dismiss": "Dismiss",
    "No account": "No account",
    "Pick or type an account first.": "Pick or type an account first.",
    "GiaoIT Bridge": "GiaoIT Bridge",
}
