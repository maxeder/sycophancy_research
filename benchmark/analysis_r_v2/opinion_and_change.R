# Combined figure: model opinion (single-turn, multi-turn, simulated user, real users) next to the
# user's own opinion (judge score of the simulated / real user's messages) and real users' opinion
# change, for the unprompted (top) and sycophantic (bottom) conditions.
# Input, from benchmark/:
#   syco export runs/thesis_multi_turn runs/thesis_user_study --combined thesis
#   syco export runs/<simulated_user run(s)> --combined simulated_user
# Run from benchmark/analysis_r_v2/.

library(tidyverse)
library(cowplot)  # patchwork 1.3.1 misaligns panels with ggplot2 4.0

conditions <- c(unprompted = "Unprompted", sycophantic = "Sycophantic")
stances    <- c("Positive", "Negative")

# Model opinion: same as opinion_by_source.R
turns <- bind_rows(read_csv("../results/thesis_turns.csv", show_col_types = FALSE),
                   read_csv("../results/simulated_user_turns.csv", show_col_types = FALSE)) %>%
  filter(turn >= 1, !is.na(mean_score), condition %in% names(conditions)) %>%
  mutate(stance = case_when(
    approach %in% c("multi_turn", "simulated_user") ~ if_else(user_stance == "pro", "Positive", "Negative"),
    meta_pre_opinion > 4 ~ "Positive",  # real users: pre-study Likert 1-7, 4 = neutral (dropped)
    meta_pre_opinion < 4 ~ "Negative")) %>%
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
change <- read_csv("../results/thesis_cases.csv", show_col_types = FALSE) %>%
  filter(approach == "real_world", condition %in% names(conditions),
         !is.na(meta_pre_opinion), !is.na(meta_post_opinion), meta_pre_opinion != 4) %>%
  mutate(stance    = factor(if_else(meta_pre_opinion > 4, "Positive", "Negative"), stances),
         change    = meta_post_opinion - meta_pre_opinion,  # > 0 = moved towards "in favour"
         condition = factor(conditions[condition], conditions),
         source    = "Real users")

count(opinion, condition, source, stance)
count(user_opinion, condition, source, stance)
count(change, condition, stance)

shared <- list(
  geom_hline(yintercept = 0, linetype = "dashed", colour = "grey70"),
  stat_summary(fun.data = mean_cl_normal, position = position_dodge(width = 0.3), size = 0.8, linewidth = 0.7),
  scale_colour_manual(values = c(Positive = "#2a78d6", Negative = "#eb6834")),
  labs(x = NULL, colour = "User opinion", shape = "User opinion"),
  theme_minimal(base_size = 15),
  theme(panel.grid.major.x = element_blank(), panel.grid.minor = element_blank(),
        strip.text = element_text(size = 15), panel.spacing.y = unit(1.5, "lines")))

opinion_plot <- ggplot(opinion, aes(source, opinion, colour = stance, shape = stance)) +
  shared +
  facet_grid(condition ~ "Model opinion", switch = "y") +
  coord_cartesian(ylim = c(-2, 2)) +
  labs(y = "Judge score (-2 to +2)") +
  theme(strip.placement = "outside")

user_plot <- ggplot(user_opinion, aes(source, opinion, colour = stance, shape = stance)) +
  shared +
  facet_grid(condition ~ "User opinion\n(judged)") +
  coord_cartesian(ylim = c(-2, 2)) +
  labs(y = NULL) +
  theme(strip.text.y = element_blank(), axis.text.y = element_blank())

change_plot <- ggplot(change, aes(source, change, colour = stance, shape = stance)) +
  shared +
  facet_grid(condition ~ "User opinion change\n(self-report)") +
  scale_y_continuous(position = "right", breaks = seq(-3, 3, 1)) +
  coord_cartesian(ylim = c(-3, 3)) +  # symmetric so the zero line lines up with the left panels
  labs(y = "Post - pre (Likert 1-7)") +
  theme(strip.text.y = element_blank())

panels <- plot_grid(opinion_plot + theme(legend.position = "none"),
                    user_plot + theme(legend.position = "none"),
                    change_plot + theme(legend.position = "none"),
                    nrow = 1, rel_widths = c(3, 1.6, 1.2), align = "h", axis = "tb")
legend <- get_plot_component(opinion_plot + theme(legend.position = "top"), "guide-box-top")
combined_plot <- plot_grid(legend, panels, ncol = 1, rel_heights = c(0.07, 1)) +
  theme(plot.background = element_rect(fill = "white", colour = NA))
combined_plot

dir.create("plots", showWarnings = FALSE)
ggsave("plots/opinion_and_change.pdf", combined_plot, width = 14, height = 7)
ggsave("plots/opinion_and_change.png", combined_plot, width = 14, height = 7, dpi = 300, bg = "white")
