# Real users' opinion change (post - pre) for positive vs. negative users, by model condition.
# Only the user study has measured opinions; simulated multi-turn users follow a fixed script.
# Input (one row per conversation), from benchmark/:
#   syco export runs/thesis_multi_turn runs/thesis_user_study --combined thesis
# Run from benchmark/analysis_r_v2/.

library(tidyverse)

change <- read_csv("../results/thesis_cases.csv", show_col_types = FALSE) %>%
  filter(approach == "real_world", !is.na(meta_pre_opinion), !is.na(meta_post_opinion)) %>%
  mutate(stance = case_when(
    meta_pre_opinion > 4 ~ "Positive",  # pre-study Likert 1-7, 4 = neutral (dropped)
    meta_pre_opinion < 4 ~ "Negative")) %>%
  filter(!is.na(stance)) %>%
  mutate(change    = meta_post_opinion - meta_pre_opinion,  # > 0 = moved towards "in favour"
         condition = factor(condition, c("unprompted", "sycophantic", "contrarian"),
                            c("Unprompted", "Sycophantic", "Contrarian")),
         stance    = factor(stance, c("Positive", "Negative")))

count(change, condition, stance)

change_plot <- ggplot(change, aes(condition, change, colour = stance, shape = stance)) +
  geom_hline(yintercept = 0, linetype = "dashed", colour = "grey70") +
  geom_point(position = position_jitterdodge(jitter.width = 0.15, jitter.height = 0.1, dodge.width = 0.4),
             alpha = 0.25, size = 1.5, show.legend = FALSE) +
  stat_summary(fun.data = mean_cl_normal, position = position_dodge(width = 0.4), size = 0.8, linewidth = 0.7) +
  scale_colour_manual(values = c(Positive = "#2a78d6", Negative = "#eb6834")) +
  scale_y_continuous(breaks = seq(-6, 6, 1)) +
  labs(x = NULL, y = "User opinion change (post - pre, Likert)", colour = "User opinion", shape = "User opinion") +
  theme_minimal(base_size = 15) +
  theme(legend.position = "top", panel.grid.major.x = element_blank(), panel.grid.minor = element_blank())
change_plot

dir.create("plots", showWarnings = FALSE)
ggsave("plots/user_opinion_change.pdf", change_plot, width = 9, height = 4.5)
ggsave("plots/user_opinion_change.png", change_plot, width = 9, height = 4.5, dpi = 300, bg = "white")
