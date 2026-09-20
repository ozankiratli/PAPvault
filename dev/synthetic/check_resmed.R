# Check a synthetic ResMed card with two readers that are not PAPvault's.
#
#   Rscript dev/synthetic/check_resmed.R [case] [session number]
#
# Without a session number it checks every session in the case, which takes
# a while when a case holds several long nights.
#
# The first reader is the R `edf` package, an implementation of the standard
# that nobody here wrote. The second is Z's own prepare_data(), which is the
# design PAPvault follows. What they decode is printed next to what
# answer.json says the card holds, so the two can be compared by eye and by
# the FAIL lines below.
#
# This checks the generator, not PAPvault: it shows the files are readable
# the way a real card is, and that the labels reach the names prepare_data()
# looks up. Whether a real ResMed card spells its labels this way is a
# separate question, and only a real card answers it.

suppressMessages({library(edf); library(tidyverse); library(lubridate); library(jsonlite)})

args <- commandArgs(trailingOnly = TRUE)
case <- if (length(args)) args[1] else "plain-night"
root <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)[1])), "..", ".."))
card <- file.path(root, "dev", "synthetic", "out", "resmed", case)
if (!dir.exists(card)) stop("no such case built: ", card)

answer <- fromJSON(file.path(card, "answer.json"), simplifyVector = FALSE)
failures <- character()
check <- function(what, got, want, tolerance = 0) {
  ok <- if (is.numeric(got) && is.numeric(want)) abs(got - want) <= tolerance else identical(got, want)
  cat(sprintf("%-28s %-26s %s\n", what, format(got), if (ok) "ok" else paste("FAIL, expected", format(want))))
  if (!ok) failures <<- c(failures, what)
}

sessions <- answer$sessions
if (length(args) > 1) sessions <- sessions[as.integer(args[2])]

for (session in sessions) {
  start <- as.POSIXct(session$start, format = "%Y-%m-%dT%H:%M:%S")
  day <- format(as.Date(session$cpap_day), "%Y%m%d")
  folder <- file.path(card, "DATALOG", day)
  stamp <- format(start, "%Y%m%d_%H%M%S")
  cat("\nsession", session$start, "in", folder, "\n")

  # 1. The independent decoder, on the file with the fastest signals.
  brp <- read.edf(file.path(folder, paste0(stamp, "_BRP.edf")))
  flow <- session$signals[["Flow.40ms"]]
  check("signal names", paste(names(brp$signal), collapse = ","), "Flow_40ms,Press_40ms")
  check("flow unit", brp$header.signal$Flow_40ms$physical.dimension, flow$unit)
  check("flow samples", length(brp$signal$Flow_40ms$data), flow$samples)
  check("flow rate", brp$header.signal$Flow_40ms$samplingrate, 1 / flow$seconds_between_samples, 1e-9)
  check("flow first value", brp$signal$Flow_40ms$data[1], flow$first_value, 1e-5)
  check("flow 100th value", brp$signal$Flow_40ms$data[100], flow$value_at_100th, 1e-5)
  check("flow last value", tail(brp$signal$Flow_40ms$data, 1), flow$last_value, 1e-5)
  check("recording ends", format(brp$header.global$timestamp.stop, "%Y-%m-%dT%H:%M:%S"), session$end)

  # 2. Z's reader, over the day's files.
  source(file.path(root, "CPAP_old", "data_prep.R"))
  # One session at a time: a day folder can hold more than one.
  files <- list.files(folder, pattern = paste0("^", stamp, ".*edf$"), full.names = TRUE)
  d <- prepare_data(files)
  check("prepare_data BRP rows", nrow(d$BRP), flow$samples)
  check("prepare_data first time", format(d$BRP$RealTime[1], "%Y-%m-%dT%H:%M:%S"), session$start)
  events <- d$EVE.events
  check("event count", nrow(events), length(session$events))
  for (i in seq_along(session$events)) {
    want <- session$events[[i]]
    check(paste0("event ", i, " text"), as.character(events$annotation[i]), want$text)
    check(paste0("event ", i, " start"), format(events$start[i], "%Y-%m-%dT%H:%M:%S"), want$start)
    check(paste0("event ", i, " duration"), events$duration[i], want$duration, 1e-9)
  }
}

cat("\n")
if (length(failures)) {
  cat("FAILED:", length(failures), "checks:", paste(failures, collapse = "; "), "\n")
  quit(status = 1)
}
cat("every check passed for case", case, "\n")
