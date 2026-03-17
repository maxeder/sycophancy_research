# Validation: LLM judge vs. human annotation agreement
# Primary metric: linear weighted Cohen's Kappa (sentence-level)
#
# Required packages: jsonlite, irr, dplyr
# Install with: install.packages(c("jsonlite", "irr", "dplyr"))

library(jsonlite)
library(irr)
library(dplyr)

HUMAN_FILE <- "../human_annotation_data/comparison_human_data.json"
JUDGE_FILE  <- "../human_annotation_data/comparison_data_judge.json"
LABELS      <- c(-2L, -1L, 0L, 1L, 2L)

# ── Data loading ──────────────────────────────────────────────────────────────

load_paired_scores <- function(human_data, judge_data) {
  judge_index <- setNames(judge_data, sapply(judge_data, `[[`, "case_id"))
  
  records <- list()
  
  for (h_entry in human_data) {
    cid     <- h_entry$case_id
    j_entry <- judge_index[[cid]]
    
    if (is.null(j_entry)) {
      warning(sprintf("case_id '%s' found in human data but missing from judge data; skipping.", cid))
      next
    }
    
    j_turns <- setNames(
      j_entry$classified_response,
      sapply(j_entry$classified_response, `[[`, "turn")
    )
    
    for (h_turn in h_entry$classified_response) {
      turn_num <- as.character(h_turn$turn)
      j_turn   <- j_turns[[turn_num]]
      
      if (is.null(j_turn)) {
        warning(sprintf("Turn %s missing in judge data for case '%s'; skipping.", turn_num, cid))
        next
      }
      
      h_sents <- h_turn$sentence_classifications
      j_sents <- j_turn$sentence_classifications
      
      if (length(h_sents) != length(j_sents)) {
        stop(sprintf(
          "Sentence count mismatch in case '%s', turn %s: human=%d, judge=%d. Cannot safely align.",
          cid, turn_num, length(h_sents), length(j_sents)
        ))
      }
      
      for (i in seq_along(h_sents)) {
        records[[length(records) + 1L]] <- data.frame(
          case_id  = cid,
          turn     = h_turn$turn,
          sentence = h_sents[[i]]$sentence,
          human    = as.integer(h_sents[[i]]$score),
          judge    = as.integer(j_sents[[i]]$score),
          stringsAsFactors = FALSE
        )
      }
    }
  }
  
  bind_rows(records)
}

# ── Statistics ────────────────────────────────────────────────────────────────

kappa_stats <- function(human, judge) {
  if (length(unique(c(human, judge))) < 2L) {
    # irr::kappa2 requires at least two distinct values
    return(data.frame(
      weighted_kappa = NA_real_,
      kappa          = NA_real_,
      mae            = mean(abs(human - judge)),
      pct_exact      = mean(human == judge),
      n              = length(human),
      note           = "single label — kappa undefined"
    ))
  }
  
  ratings <- cbind(human, judge)
  kw <- irr::kappa2(ratings, weight = "equal")          # linear weighted
  ku <- irr::kappa2(ratings, weight = "unweighted")
  
  data.frame(
    weighted_kappa = kw$value,
    kappa          = ku$value,
    mae            = mean(abs(human - judge)),
    pct_exact      = mean(human == judge),
    n              = length(human),
    note           = NA_character_
  )
}

fmt_stats <- function(stats) {
  if (!is.na(stats$note)) {
    return(sprintf("  [%s]  MAE = %.3f | exact = %.1f%% | n = %d",
                   stats$note, stats$mae, stats$pct_exact * 100, stats$n))
  }
  sprintf(
    "  weighted κ = %.3f | κ = %.3f | MAE = %.3f | exact = %.1f%% | n = %d",
    stats$weighted_kappa, stats$kappa, stats$mae, stats$pct_exact * 100, stats$n
  )
}

print_confusion <- function(human, judge) {
  cm <- table(
    factor(human, levels = LABELS),
    factor(judge, levels = LABELS)
  )
  dimnames(cm) <- list(
    paste0("H=", ifelse(LABELS >= 0, "+", ""), LABELS),
    paste0("J=", ifelse(LABELS >= 0, "+", ""), LABELS)
  )
  print(cm)
}

print_score_dist <- function(scores, label) {
  counts <- table(factor(scores, levels = LABELS))
  total  <- length(scores)
  parts  <- paste(
    sprintf("%+d: %3d (%.1f%%)", LABELS, as.integer(counts), as.integer(counts) / total * 100),
    collapse = "  "
  )
  cat(sprintf("  %s: %s\n", label, parts))
}

# ── Load ──────────────────────────────────────────────────────────────────────

human_data <- fromJSON(HUMAN_FILE, simplifyVector = FALSE)
judge_data  <- fromJSON(JUDGE_FILE,  simplifyVector = FALSE)

records <- load_paired_scores(human_data, judge_data)

# Guard: flag any out-of-range scores before analysis
bad <- records |>
  filter(!human %in% LABELS | !judge %in% LABELS)
if (nrow(bad) > 0L) {
  warning(sprintf("%d record(s) have scores outside {-2,-1,0,1,2} and will distort kappa.", nrow(bad)))
}

# ── Global ────────────────────────────────────────────────────────────────────

cat(strrep("=", 70), "\n")
cat("GLOBAL\n")
cat(strrep("=", 70), "\n")

stats_global <- kappa_stats(records$human, records$judge)
cat(fmt_stats(stats_global), "\n")

cat("\nScore distributions:\n")
print_score_dist(records$human, "human")
print_score_dist(records$judge, "judge")

cat("\nConfusion matrix (rows = human, cols = judge):\n")
print_confusion(records$human, records$judge)

# ── Per case ──────────────────────────────────────────────────────────────────

cat("\n", strrep("=", 70), "\n", sep = "")
cat("PER CASE\n")
cat(strrep("=", 70), "\n")

for (cid in unique(records$case_id)) {
  sub   <- filter(records, case_id == cid)
  stats <- kappa_stats(sub$human, sub$judge)
  cat(sprintf("\n%s\n", cid))
  cat(fmt_stats(stats), "\n")
}

# ── Per turn ──────────────────────────────────────────────────────────────────

cat("\n", strrep("=", 70), "\n", sep = "")
cat("PER TURN\n")
cat(strrep("=", 70), "\n")

for (t in sort(unique(records$turn))) {
  sub   <- filter(records, turn == t)
  stats <- kappa_stats(sub$human, sub$judge)
  cat(sprintf("\nTurn %d\n", t))
  cat(fmt_stats(stats), "\n")
}






# Confusion matrix plot: LLM judge vs. human annotation
#
# Run after (or alongside) agreement_analysis.R.
# Requires: ggplot2, dplyr, scales
# Install with: install.packages(c("ggplot2", "dplyr", "scales"))

library(ggplot2)
library(dplyr)
library(scales)

# ── Build the confusion data frame ────────────────────────────────────────────
# `records` must already exist in the environment (from agreement_analysis.R).
# If running standalone, source that script first:
#   source("agreement_analysis.R")

LABELS <- c(-2L, -1L, 0L, 1L, 2L)
label_fmt <- function(x) ifelse(x >= 0, paste0("+", x), as.character(x))

cm_df <- records |>
  mutate(
    human = factor(label_fmt(human), levels = label_fmt(LABELS)),
    judge = factor(label_fmt(judge), levels = label_fmt(LABELS))
  ) |>
  count(human, judge, name = "n") |>
  # complete so empty cells appear as 0
  tidyr::complete(human, judge, fill = list(n = 0L)) |>
  group_by(human) |>
  mutate(
    row_total = sum(n),
    pct       = if_else(row_total > 0, n / row_total, 0)  # row-normalised %
  ) |>
  ungroup()

# ── Plot ──────────────────────────────────────────────────────────────────────

p <- ggplot(cm_df, aes(x = judge, y = human, fill = pct)) +
  
  # tiles
  geom_tile(colour = "white", linewidth = 1.2) +
  
  # count label (large)
  geom_text(
    aes(label = n),
    colour   = "white",
    fontface = "bold",
    size     = 5.5
  ) +
  
  # row-% label (small, below count)
  geom_text(
    aes(label = if_else(n > 0, scales::percent(pct, accuracy = 1), "")),
    colour = "white",
    size   = 3.2,
    vjust  = 2.8,
    alpha  = 0.85
  ) +
  
  scale_fill_gradientn(
    colours = c("#1e2d40", "#1b5fa8", "#2196f3", "#64b5f6"),
    limits  = c(0, 1),
    labels  = scales::percent,
    name    = "Row %"
  ) +
  
  scale_x_discrete(position = "top") +
  
  labs(
    title    = "LLM Judge vs. Human Annotation",
    # subtitle = "Sentence-level scores  ·  rows = human  ·  cols = judge\nCell colour = row-normalised %  ·  number = count",
    subtitle = "Sentence-level scores with rows representing human scores and columns LLM scores\nCell colour represents row-normalised percentages, numbers indicate score count",
    x        = "Judge score",
    y        = "Human score"
  ) +
  
  theme_minimal(base_size = 13) +
  theme(
    plot.title       = element_text(face = "bold", size = 15, margin = margin(b = 4)),
    plot.subtitle    = element_text(size = 10, colour = "grey45", lineheight = 1.4,
                                    margin = margin(b = 14, t=10)),
    axis.title       = element_text(face = "bold", size = 11),
    axis.text        = element_text(size = 11),
    panel.grid       = element_blank(),
    legend.position  = "right",
    legend.key.height = unit(1.8, "cm"),
    plot.margin      = margin(16, 16, 16, 16)
  ) +
  
  # diagonal guide line
  annotate(
    "rect",
    xmin = 0.5, xmax = 5.5,
    ymin = 0.5, ymax = 5.5,
    colour = "grey70", fill = NA, linewidth = 0.4, linetype = "dashed"
  ) +
  
  coord_fixed()


p
# ── Save ──────────────────────────────────────────────────────────────────────

# ggsave(
#   "confusion_matrix.png",
#   plot   = p,
#   width  = 7,
#   height = 6.5,
#   dpi    = 180,
#   bg     = "white"
# )
# 
# message("Saved → confusion_matrix.png")