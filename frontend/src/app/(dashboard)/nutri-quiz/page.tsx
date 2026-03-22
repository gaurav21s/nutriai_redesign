"use client";

import { FormEvent, useMemo, useState } from "react";
import { useUser } from "@clerk/nextjs";
import { Sparkles, Trophy, Brain, ChevronRight, Check } from "lucide-react";

import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { ResultBlock } from "@/components/features/result-block";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FieldLabel } from "@/components/ui/field-label";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useApiClient } from "@/hooks/useApiClient";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { useConvexHistory } from "@/hooks/useConvexHistory";
import type { QuizDifficulty, QuizHistoryItem, QuizSessionResponse, QuizSubmitResponse } from "@/types/api";

export default function NutriQuizPage() {
  const api = useApiClient();
  const { user } = useUser();

  const [topic, setTopic] = useState("Nutrition");
  const [difficulty, setDifficulty] = useState<QuizDifficulty>("easy");
  const [session, setSession] = useState<QuizSessionResponse | null>(null);
  const [submission, setSubmission] = useState<QuizSubmitResponse | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [sortBy, setSortBy] = useState<"date_desc" | "date_asc" | "score_desc" | "topic_asc">("date_desc");

  const { data: history, loading: historyLoading, refreshInBackground } = useConvexHistory<QuizHistoryItem>({
    functionName: "quizzes:listHistory",
    clerkUserId: user?.id,
    limit: 20,
    pollIntervalMs: 20000,
  });

  const generateAction = useAsyncAction(async () => api.generateQuiz(topic, difficulty, 5));
  const submitAction = useAsyncAction(async () => {
    if (!session) throw new Error("Generate a quiz first");
    const payload = session.questions.map((_, index) => ({
      question_index: index,
      selected_option: answers[index] ?? "",
    }));
    return api.submitQuiz(session.session_id, payload);
  });

  const canSubmit = useMemo(() => {
    if (!session) return false;
    return session.questions.every((_, index) => Boolean(answers[index]));
  }, [answers, session]);

  const sortedHistory = useMemo(() => {
    const items = [...history];
    if (sortBy === "date_asc") {
      return items.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    }
    if (sortBy === "score_desc") {
      return items.sort((a, b) => (b.score_percentage ?? -1) - (a.score_percentage ?? -1));
    }
    if (sortBy === "topic_asc") {
      return items.sort((a, b) => a.topic.localeCompare(b.topic));
    }
    return items.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }, [history, sortBy]);

  async function handleGenerate(event: FormEvent) {
    event.preventDefault();
    const generated = await generateAction.execute();
    if (!generated) return;
    setSession(generated);
    setSubmission(null);
    setAnswers({});
    refreshInBackground();
  }

  async function handleSubmitQuiz() {
    const result = await submitAction.execute();
    if (result) {
      setSubmission(result);
      refreshInBackground();
    }
  }

  return (
    <FeatureShell
      title="Nutri Quiz"
      description="Take quick quizzes by topic, then track your scores over time."
      aside={
        <HistoryPanel
          title="Score Tracker"
          loading={historyLoading}
          empty={!history.length}
          syncing={generateAction.loading || submitAction.loading}
        >
          <div className="mb-8">
            <FieldLabel htmlFor="quiz-sort">Sort by</FieldLabel>
            <Select
              id="quiz-sort"
              value={sortBy}
              className="bg-white/40 border-black/[0.05] text-[10px] font-bold uppercase tracking-widest mt-2"
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            >
              <option value="date_desc">Latest first</option>
              <option value="date_asc">Oldest first</option>
              <option value="score_desc">Highest score</option>
              <option value="topic_asc">Topic A-Z</option>
            </Select>
          </div>

          <div className="space-y-4">
            {sortedHistory.map((item) => (
              <div key={item.session_id} className="rounded-editorial border border-black/[0.03] bg-white/40 p-4 shadow-soft-glow transition-all hover:bg-white/60 group">
                <div className="flex items-center gap-3 mb-2">
                  <Brain className="h-3.5 w-3.5 text-vibrant/40 group-hover:text-vibrant transition-colors" />
                  <p className="text-sm font-semibold text-foreground group-hover:text-vibrant transition-colors truncate">{item.topic}</p>
                </div>
                <div className="flex justify-between items-end">
                  <p className="text-[9px] font-bold uppercase tracking-widest text-foreground/20">
                    {item.difficulty} • {new Date(item.created_at).toLocaleDateString()}
                  </p>
                  <p className="text-xs font-display italic font-bold text-vibrant">
                    {item.score_percentage != null ? `${item.score_percentage.toFixed(0)}%` : "??%"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </HistoryPanel>
      }
    >
      <form className="grid gap-6 sm:grid-cols-[1fr_180px_auto]" onSubmit={handleGenerate}>
        <div className="space-y-2">
          <FieldLabel htmlFor="quiz-topic">Topic</FieldLabel>
          <Select
            id="quiz-topic"
            value={topic}
            className="bg-white/50 border-black/[0.05] focus:border-vibrant transition-all"
            onChange={(event) => setTopic(event.target.value)}
          >
            <option value="Nutrition">Nutrition</option>
            <option value="Yoga">Yoga</option>
            <option value="Gym">Strength & Conditioning</option>
            <option value="Food">Food</option>
            <option value="Supplements">Supplements</option>
            <option value="Lifestyle">Lifestyle</option>
          </Select>
        </div>
        <div className="space-y-2">
          <FieldLabel htmlFor="quiz-difficulty">Difficulty</FieldLabel>
          <Select
            id="quiz-difficulty"
            value={difficulty}
            className="bg-white/50 border-black/[0.05] focus:border-vibrant transition-all"
            onChange={(event) => setDifficulty(event.target.value as QuizDifficulty)}
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </Select>
        </div>
        <div className="pt-[22px]">
          <Button type="submit" size="lg" className="rounded-full bg-vibrant hover:bg-vibrant/90 text-white shadow-soft-glow px-10" disabled={generateAction.loading}>
            {generateAction.loading ? "Generating..." : "Start Quiz"}
          </Button>
        </div>
      </form>

      {generateAction.error ? <Alert variant="error" className="mt-8 rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{generateAction.error}</Alert> : null}

      {session ? (
        <div className="mt-12 space-y-8 animate-reveal">
          <ResultBlock title="Questions">
            <div className="space-y-8">
              {session.questions.map((question, index) => (
                <div key={`${question.question}-${index}`} className="rounded-editorial border border-black/[0.03] bg-white/40 p-8 shadow-soft-glow">
                  <div className="flex gap-4 mb-6">
                    <span className="text-vibrant font-display italic text-2xl leading-none">Q{index + 1}.</span>
                    <p className="text-lg font-medium text-foreground leading-[1.4]">{question.question}</p>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    {question.options.map((option, optionIndex) => {
                      const optionCode = String.fromCharCode(65 + optionIndex);
                      const isSelected = answers[index] === optionCode;
                      return (
                        <label
                          key={`${option}-${optionIndex}`}
                          className={`flex items-center gap-4 rounded-full border px-6 py-4 text-sm font-semibold transition-all cursor-pointer shadow-sm ${isSelected ? "border-vibrant bg-vibrant/5 text-vibrant ring-1 ring-vibrant/20" : "border-black/[0.05] bg-white/80 text-foreground/60 hover:border-vibrant/20 hover:text-foreground"
                            }`}
                        >
                          <input
                            type="radio"
                            className="hidden"
                            name={`question-${index}`}
                            value={optionCode}
                            checked={isSelected}
                            onChange={() => setAnswers((prev) => ({ ...prev, [index]: optionCode }))}
                          />
                          <div className={`h-6 w-6 rounded-full border flex items-center justify-center text-[10px] uppercase font-bold tracking-widest ${isSelected ? "bg-vibrant text-white border-vibrant" : "bg-black/[0.05] border-transparent text-foreground/40"
                            }`}>
                            {optionCode}
                          </div>
                          <span>{option}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-12 flex items-center justify-between p-8 bg-vibrant/5 border border-vibrant/10 rounded-editorial">
              <div className="space-y-1">
                <p className="text-xs font-bold uppercase tracking-widest text-vibrant flex items-center gap-2">
                  <Trophy className="h-3 w-3" />
                  Ready To Submit
                </p>
                <p className="text-sm text-vibrant/60 font-medium italic">All questions have answers.</p>
              </div>
              <Button type="button" size="lg" className="rounded-full bg-vibrant text-white px-12 hover:bg-vibrant/90 shadow-soft-glow" onClick={handleSubmitQuiz} disabled={!canSubmit || submitAction.loading}>
                {submitAction.loading ? "Checking..." : "Submit Quiz"}
              </Button>
            </div>
          </ResultBlock>

          {submitAction.error ? <Alert variant="error" className="rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{submitAction.error}</Alert> : null}

          {submission ? (
            <div className="animate-reveal">
              <ResultBlock title={`Score: ${submission.correct_answers}/${submission.total_questions} (${submission.score_percentage.toFixed(1)}%)`}>
                <div className="grid gap-6">
                  {submission.results.map((item) => (
                    <div
                      key={item.question_index}
                      className={`rounded-editorial border p-6 shadow-soft-glow transition-all ${item.is_correct ? "border-success-500/20 bg-success-50/5" : "border-vibrant/10 bg-vibrant/5 opacity-90"
                        }`}
                    >
                      <div className="flex justify-between items-start mb-4">
                        <p className="text-sm font-bold text-foreground">
                          Question {item.question_index + 1}
                        </p>
                        <Badge className={`rounded-full px-4 py-1 text-[9px] uppercase font-bold tracking-widest ${item.is_correct ? "bg-success-600 border-none text-white" : "bg-vibrant border-none text-white"
                          }`}>
                          {item.is_correct ? "Correct" : "Incorrect"}
                        </Badge>
                      </div>
                      <div className="space-y-3">
                        <p className={`text-xs font-bold uppercase tracking-widest ${item.is_correct ? "text-success-700" : "text-vibrant"}`}>
                          Answer: {item.selected_option || "-"} vs {item.correct_option}
                        </p>
                        <div className="p-4 bg-white/40 rounded-xl text-xs font-medium text-foreground/60 leading-relaxed italic border border-black/[0.02]">
                          {item.explanation}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ResultBlock>
            </div>
          ) : null}
        </div>
      ) : null}
    </FeatureShell>
  );
}
