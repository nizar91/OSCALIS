json = dofile(reaper.GetResourcePath() .. "/Scripts/dkjson.lua")
local lastData = ""
local lastSendTime = 0
local instrumentFile = reaper.GetResourcePath() .. "/instrument_changes.json"
local inputFile = reaper.GetResourcePath() .. "/input_changes.json"
local outputFile = reaper.GetResourcePath() .. "/tracks.json"

local availableInstruments = {
    "DSK Strings (x86) (DSK Music)",
    "Electric (AIR Music Technology)",
    "Hype (AIR Music Technology)",
    "MPC Beats (Akai Professional)",
    "Pianoteq 8 (Modartt)",
    "ReaSamplOmatic5000 (Cockos)",
    "ReaSynDr (Cockos)",
    "ReaSynth (Cockos)"
}

function applyInstrumentToTrack(track, instrument)
    if not instrument or instrument == "" then return end
    local fxIndex = reaper.TrackFX_AddByName(track, instrument, false, 1)
    if fxIndex >= 0 then
        reaper.TrackFX_Show(track, fxIndex, 3)
    end
end

function loadInstrumentsMap()
    local f = io.open(instrumentFile, "r")
    if not f then return {} end
    local content = f:read("*all")
    f:close()
    local result, _, err = json.decode(content)
    if err then return {} end
    return result or {}
end

function loadInputChanges()
    local f = io.open(inputFile, "r")
    if not f then return {} end
    local content = f:read("*all")
    f:close()
    local result, _, err = json.decode(content)
    if err then return {} end
    return result or {}
end

function getTrackData()
    local trackCount = reaper.CountTracks(0)
    local trackList = {}
    local instrumentMap = loadInstrumentsMap()
    local inputChanges = loadInputChanges()

    for i = 0, trackCount - 1 do
        local track = reaper.GetTrack(0, i)
        local _, name = reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "", false)
        local volume = reaper.GetMediaTrackInfo_Value(track, "D_VOL")
        local pan = reaper.GetMediaTrackInfo_Value(track, "D_PAN")
        local isMuted = reaper.GetMediaTrackInfo_Value(track, "B_MUTE") == 1
        local isArmed = reaper.GetMediaTrackInfo_Value(track, "I_RECARM") == 1
        local input = reaper.GetMediaTrackInfo_Value(track, "I_RECINPUT")
        local id = tostring(i + 1)
        local inst = instrumentMap[id]

        -- Appliquer les modifications d'input si présentes
        local newInput = inputChanges[id]
        if newInput then
            reaper.SetMediaTrackInfo_Value(track, "I_RECINPUT", tonumber(newInput))
            input = tonumber(newInput)  -- pour l'affichage dans le JSON
        end

        if inst then
            applyInstrumentToTrack(track, inst)
        end

        table.insert(trackList, string.format(
            '{"id": %d, "name": "%s", "volume": %.3f, "pan": %.3f, "instrument": "%s", "enabled": %s, "record": %s, "input": %d}',
            i + 1,
            name:gsub('"', '\\"'),
            volume,
            pan,
            (inst or ""):gsub('"', '\\"'),
            tostring(not isMuted),
            tostring(isArmed),
            input
        ))
    end

    local instrumentList = {}
    for _, name in ipairs(availableInstruments) do
        table.insert(instrumentList, string.format('"%s"', name:gsub('"', '\\"')))
    end

    return string.format(
        '{"tracks": [%s], "instruments": [%s]}',
        table.concat(trackList, ","), table.concat(instrumentList, ",")
    )
end

function saveTrackData()
    local jsonData = getTrackData()
    local currentTime = os.time()

    if jsonData ~= lastData or (currentTime - lastSendTime) >= 2 then
        lastData = jsonData
        lastSendTime = currentTime

        local f = io.open(outputFile, "w+")
        if f then
            f:write(jsonData)
            f:close()
        end
    end

    reaper.defer(saveTrackData)
end

saveTrackData()