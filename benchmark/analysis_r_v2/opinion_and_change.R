# Combined figure: model opinion (single-turn, multi-turn, simulated user, real users) next to the
# user's own opinion (judge score of the simulated / real user's messages) and real users' opinion
# change, for the sycophantic (top) and unprompted (bottom) conditions. Sized for a 16:9 slide.
# Input: results/<run>/turns.csv for each run in `runs`, and results/thesis_user_study/cases.csv.
# Regenerate from benchmark/ with: syco export runs/*
# Run from benchmark/analysis_r_v2/.

library(tidyverse)
library(cowplot)  # patchwork 1.3.1 misaligns panels with ggplot2 4.0

runs       <- c("thesis_multi_turn", "thesis_user_study", "2026-10-08_simulated_user_pilot_openai_gpt-5.2_cc82b0")
conditions <- c(sycophantic = "Sycophantic", unprompted = "Unprompted")  # rows, top to bottom
stances    <- c("Pro", "Contra")
font       <- c(intersect(c("Arial", "Inter"), systemfonts::system_fonts()$family), "")[1]  # "" = R's default sans
set_null_device("agg")  # cowplot measures text with ragg, which knows system fonts (its pdf default does not)

# Model opinion: same as opinion_by_source.R
turns <- map(runs, \(r) read_csv(file.path("../results", r, "turns.csv"), show_col_types = FALSE)) %>%
  bind_rows() %>%
  filter(turn >= 1, !is.na(mean_score), condition %in% names(conditions)) %>%
  mutate(stance = case_when(
    approach %in% c("multi_turn", "simulated_user") ~ if_else(user_stance == "pro", "Pro", "Contra"),
    meta_pre_opinion > 4 ~ "Pro",  # real users: pre-study Likert 1-7, 4 = neutral (dropped)
    meta_pre_opinion < 4 ~ "Contra")) %>%
  filter(!is.na(stance))
assistant <- filter(turns, role == "assistant")

opinion <- bind_rows(
  `Single-turn` = filter(assistant, approach == "multi_turn", turn == 1),
  `Multi-turn`  = filter(assistant, approach == "multi_turn"),
  `Simulated user` = filter(assistant, approach == "simulated_user"),
  `Real users`  = filter(assistant, approach == "real_world"),
  .id = "source") %>%
  group_by(source, condition, stance, case_id) %>%
  summarise(opinion = mean(mean_score), .groups = "drop") %>%
  mutate(source    = factor(source, c("Single-turn", "Multi-turn", "Simulated user", "Real users")),
         condition = factor(conditions[condition], conditions),
         stance    = factor(stance, stances))

# User opinion: judge score of the user's own messages, on the same scale as the model opinion
# (turn >= 1 drops the simulated user's neutral turn-0 question)
user_opinion <- turns %>%
  filter(role == "user", approach %in% c("simulated_user", "real_world")) %>%
  mutate(source = if_else(approach == "simulated_user", "Simulated user", "Real users")) %>%
  group_by(source, condition, stance, case_id) %>%
  summarise(opinion = mean(mean_score), .groups = "drop") %>%
  mutate(source    = factor(source, c("Simulated user", "Real users")),
         condition = factor(conditions[condition], conditions),
         stance    = factor(stance, stances))

# User opinion change: same as user_opinion_change.R
change <- read_csv("../results/thesis_user_study/cases.csv", show_col_types = FALSE) %>%
  filter(approach == "real_world", condition %in% names(conditions),
         !is.na(meta_pre_opinion), !is.na(meta_post_opinion), meta_pre_opinion != 4) %>%
  mutate(stance    = factor(if_else(meta_pre_opinion > 4, "Pro", "Contra"), stances),
         change    = meta_post_opinion - meta_pre_opinion,  # > 0 = moved towards "pro"
         source    = factor("Real users"),
         condition = factor(conditions[condition], conditions))

count(opinion, condition, source, stance)
count(user_opinion, condition, source, stance)
count(change, condition, stance)

# Signed tick labels with a true minus sign; the judge axis names its poles
signed      <- function(x) case_when(x > 0 ~ paste0("+", x), x < 0 ~ paste0("−", abs(x)), .default = "0")
score_ticks <- c("Contra  −2", "−1", "0", "+1", "Pro  +2")
text_size   <- 18

shared <- list(
  geom_hline(yintercept = 0, colour = "grey55", linewidth = 0.5),
  stat_summary(fun.data = mean_cl_normal, position = position_dodge(width = 0.35), size = 0.9, linewidth = 0.8),
  facet_wrap(~ condition, ncol = 1),
  scale_colour_manual(values = c(Pro = "#2a78d6", Contra = "#eb6834")),
  labs(x = NULL, y = NULL, colour = "User stance"),
  theme_minimal(base_size = text_size, base_family = font),
  theme(panel.grid.major.x = element_blank(), panel.grid.minor = element_blank(),
        panel.grid.major.y = element_line(colour = "grey90", linewidth = 0.4),
        plot.title = element_text(size = rel(1), hjust = 0.5, lineheight = 1.05, margin = margin(b = 8)),
        strip.text = element_text(face = "bold", size = rel(1.05), hjust = 0, margin = margin(t = 4, b = 8)),
        axis.text = element_text(colour = "grey25"),
        panel.spacing.y = unit(1.6, "lines"),
        legend.position = "none"))

hide_strip_text <- theme(strip.text = element_text(colour = "transparent"))  # keeps the strip height, so rows align

opinion_plot <- ggplot(opinion, aes(source, opinion, colour = stance)) +
  shared +
  scale_y_continuous(breaks = -2:2, labels = score_ticks) +
  coord_cartesian(ylim = c(-2, 2)) +
  labs(title = "Model opinion\n(judge score)")

user_plot <- ggplot(user_opinion, aes(source, opinion, colour = stance)) +
  shared +
  scale_y_continuous(breaks = -2:2) +
  coord_cartesian(ylim = c(-2, 2)) +
  labs(title = "User opinion\n(judge score)") +
  hide_strip_text +
  theme(axis.text.y = element_blank())

change_plot <- ggplot(change, aes(source, change, colour = stance)) +
  shared +
  scale_y_continuous(position = "right", breaks = -3:3, labels = signed) +
  coord_cartesian(ylim = c(-3, 3)) +  # symmetric so the zero line lines up with the left panels
  labs(title = "User opinion change\n(self-report)", y = "Post − pre (Likert 1–7)") +
  hide_strip_text +
  theme(plot.margin = margin(l = 30, r = 5))

panels <- plot_grid(opinion_plot, user_plot, change_plot,
                    nrow = 1, rel_widths = c(3.3, 1.6, 1.45), align = "h", axis = "tb")
legend <- get_plot_component(opinion_plot + theme(legend.position = "top"), "guide-box-top")
combined_plot <- plot_grid(legend, panels, ncol = 1, rel_heights = c(0.07, 1)) +
  theme(plot.background = element_rect(fill = "white", colour = NA))
combined_plot

# 13.33 x 7.5 in = a full 16:9 slide. cairo_pdf needs XQuartz on macOS; the Quartz PDF device
# embeds system fonts without it
pdf_device <- if (capabilities("aqua")) \(filename, ...) grDevices::quartz(type = "pdf", file = filename, ...) else cairo_pdf
dir.create("plots", showWarnings = FALSE)
ggsave("plots/opinion_and_change.pdf", combined_plot, width = 13.333, height = 7.5, device = pdf_device)
ggsave("plots/opinion_and_change.png", combined_plot, width = 13.333, height = 7.5, dpi = 300, bg = "white")
