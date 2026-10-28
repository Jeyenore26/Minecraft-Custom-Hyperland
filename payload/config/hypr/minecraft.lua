-- Ancient City / Minecraft desktop — Hyprland 0.56 Lua configuration.
local home = os.getenv("HOME")
local root = home .. "/.config/hypr/minecraft/"
local function quote(value) return "'" .. value:gsub("'", "'\"'\"'") .. "'" end
local terminal = "/usr/bin/kitty --config " .. quote(root .. "kitty.conf")
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })
hl.env("XCURSOR_SIZE", "24")
hl.env("XCURSOR_THEME", "Adwaita")
hl.env("GTK_THEME", "Minecraft-DeepSlate")
hl.config({
 general = {
  gaps_in = 6, gaps_out = 14, border_size = 3,
  col = { active_border = "rgba(8cce87ff)", inactive_border = "rgba(405850ff)" },
  resize_on_border = true, allow_tearing = false, layout = "dwindle",
 },
 decoration = {
  rounding = 0, active_opacity = 1.0, inactive_opacity = 0.98,
  shadow = { enabled = true, range = 14, render_power = 3, color = 0x99091014 },
  blur = { enabled = true, size = 4, passes = 2 },
 },
 animations = { enabled = true },
 debug = { suppress_errors = true },
 input = {
  kb_layout = "us,eg", kb_options = "grp:alt_shift_toggle",
  follow_mouse = 1, sensitivity = 0,
  touchpad = { natural_scroll = true, tap_to_click = true },
 },
 dwindle = { preserve_split = true },
 misc = { disable_hyprland_logo = true, force_default_wallpaper = 0 },
})
hl.curve("craft", { type = "bezier", points = { {0.16, 1}, {0.3, 1} } })
hl.animation({ leaf = "windows", enabled = true, speed = 3, bezier = "craft", style = "popin 92%" })
hl.animation({ leaf = "fade", enabled = true, speed = 2, bezier = "craft" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 3, bezier = "craft", style = "slide" })
-- Minecraft achievement toast: enter/leave from the right edge.
hl.layer_rule({ name = "minecraft-achievement-toast", match = { namespace = "^swaync-notification-window$" }, animation = "slide right", blur = true, ignore_alpha = 0.05 })
hl.layer_rule({ name = "minecraft-achievement-glass", match = { namespace = "^swaync-control-center$" }, animation = "fade", blur = true, ignore_alpha = 0.05 })
hl.layer_rule({ name = "minecraft-wandering-animal", match = { namespace = "^minecraft-wandering-animal$" }, no_anim = true })
-- Quiet the compositor's Lua runtime toasts, retaining their text for diagnosis.
-- These are separate from SwayNC and from the configuration-error overlay.
hl.timer(function()
 for _, notice in ipairs(hl.notification.get()) do
  local text = notice:get_text()
  if text and text:lower():find("runtime error in lua", 1, true) then
   local log = io.open(home .. "/.local/state/minecraft-desktop/lua-errors.log", "a")
   if log then log:write(os.date("%Y-%m-%d %H:%M:%S "), text, "\n"); log:close() end
   notice:set_text("")
   notice:dismiss()
  end
 end
end, { type = "repeat", timeout = 100 })
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
local function cmd(key, command) hl.bind(key, hl.dsp.exec_cmd(command)) end
cmd("SUPER + Return", terminal)
cmd("SUPER + Space", quote(root .. "launcher.sh"))
cmd("SUPER + R", quote(root .. "launcher.sh"))
cmd("SUPER + Tab", "/usr/bin/python3 " .. quote(root .. "windows.py"))
cmd("SUPER + E", "nautilus --new-window")
cmd("SUPER + B", "firefox")
cmd("SUPER + H", quote(root .. "guide.py"))
cmd("SUPER + comma", "/usr/bin/python3 " .. quote(root .. "settings.py"))
cmd("SUPER + L", quote(root .. "lock.sh"))
cmd("SUPER + Escape", quote(root .. "power.py"))
cmd("SUPER + N", "swaync-client -t")
cmd("SUPER + P", "/usr/bin/python3 " .. quote(root .. "display-menu.py"))
cmd("SUPER + SHIFT + S", quote(root .. "screenshot.sh"))
cmd("Print", quote(root .. "screenshot.sh"))
cmd("SUPER + SHIFT + R", "hyprctl reload")
hl.bind("SUPER + Q", hl.dsp.window.close())
hl.bind("SUPER + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind("SUPER + F", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
hl.bind("SUPER + J", hl.dsp.layout("togglesplit"))
for _,direction in ipairs({"left","right","up","down"}) do
 hl.bind("SUPER + " .. direction, hl.dsp.focus({ direction = direction }))
 hl.bind("SUPER + SHIFT + " .. direction, hl.dsp.window.move({ monitor = direction, follow = true }))
end
for i = 1, 9 do
 hl.bind("SUPER + " .. i, hl.dsp.focus({ workspace = i }))
 hl.bind("SUPER + SHIFT + " .. i, hl.dsp.window.move({ workspace = i }))
end
hl.bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })
hl.bind("SUPER + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind("SUPER + mouse_up", hl.dsp.focus({ workspace = "e-1" }))
for _,v in ipairs({
 {"XF86AudioRaiseVolume", "wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"},
 {"XF86AudioLowerVolume", "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"},
 {"XF86AudioMute", "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"},
 {"XF86AudioMicMute", "wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"},
 {"XF86MonBrightnessUp", "brightnessctl -n2 set +5%"},
 {"XF86MonBrightnessDown", "brightnessctl -n2 set 5%-"},
 {"XF86AudioPlay", "playerctl play-pause"},
 {"XF86AudioNext", "playerctl next"},
 {"XF86AudioPrev", "playerctl previous"},
}) do hl.bind(v[1], hl.dsp.exec_cmd(v[2]), { locked = true, repeating = true }) end
hl.window_rule({ name = "field-guide", match = { class = "minecraft-guide" }, float = true, size = "740 660", center = true })
hl.window_rule({ name = "pause-menu", match = { class = "minecraft-pause" }, float = true, size = "440 520", center = true })
hl.window_rule({ name = "audio-settings", match = { class = "org.pulseaudio.pavucontrol" }, float = true, size = "800 600", center = true })
hl.on("hyprland.start", function()
 if os.getenv("MC_TEST") ~= "1" then hl.exec_cmd(quote(root .. "start.sh")) end
end)

hl.window_rule({ name = "inventory", match = { class = "minecraft-inventory" }, float = true, size = "1200 552", center = true, border_size = 0, no_shadow = true, no_blur = false, no_anim = false, animation = "fade" })

-- Ask the inventory to dismiss on outside presses, preserving the original click.
-- A press (not release) keeps inventory-to-dock drag and drop uninterrupted.
for _,button in ipairs({272, 273, 274}) do
 hl.bind("mouse:" .. button, function()
  for _,window in ipairs(hl.get_windows()) do
   if window.class == "minecraft-inventory" and window.mapped then
    hl.exec_cmd("kill -USR1 " .. window.pid)
   end
  end
 end, { non_consuming = true, ignore_mods = true })
end

hl.window_rule({ name = "minecraft-wifi", match = { class = "minecraft-wifi" }, float = true, size = "760 640", center = true, border_size = 0 })

hl.window_rule({ name = "minecraft-settings", match = { class = "minecraft-settings" }, float = true, size = "520 600", center = true })
