"use client";

import { FormEvent, useMemo, useState } from "react";
import { useUser } from "@clerk/nextjs";

import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { ResultBlock } from "@/components/features/result-block";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
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
      description="Generate quizzes, submit answers, and track score trends over time."
      aside={
        <HistoryPanel
          title="Recent Quiz Attempts"
          loading={historyLoading}
          empty={!history.length}
          syncing={generateAction.loading || submitAction.loading}
        >
          {history.map((item) => (
            <div key={item.session_id} className="rounded-xl border border-surface-200 bg-surface-50 p-3">
              <p className="text-sm font-semibold text-accent-800">{item.topic}</p>
              <p className="mt-1 text-xs text-accent-600">
                {item.difficulty} • {new Date(item.created_at).toLocaleString()}
              </p>
              <p className="mt-1 text-xs font-semibold text-secondary-700">
                Score: {item.score_percentage != null ? `${item.score_percentage.toFixed(1)}%` : "Pending"}
              </p>
            </div>
          ))}
        </HistoryPanel>
      }
    >
      <form className="grid gap-3 sm:grid-cols-[1fr_180px_auto]" onSubmit={handleGenerate}>
        <Input value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="Quiz topic" />
        <Select value={difficulty} onChange={(event) => setDifficulty(event.target.value as QuizDifficulty)}>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </Select>
        <Button type="submit" disabled={generateAction.loading}>
          {generateAction.loading ? "Generating..." : "Generate Quiz"}
        </Button>
      </form>

      {generateAction.error ? <Alert variant="error">{generateAction.error}</Alert> : null}

      {session ? (
        <div className="mt-6 space-y-4">
          <ResultBlock title="Quiz Questions">
            <div className="space-y-5">
              {session.questions.map((question, index) => (
                <div key={`${question.question}-${index}`} className="rounded-xl border border-surface-200 p-4">
                  <p className="text-sm font-semibold text-accent-800">{`Q${index + 1}. ${question.question}`}</p>
                  <div className="mt-3 space-y-2">
                    {question.options.map((option, optionIndex) => {
                      const optionCode = String.fromCharCode(65 + optionIndex);
                      return (
                        <label
                          key={`${option}-${optionIndex}`}
                          className="flex items-center gap-2 rounded-lg border border-surface-200 px-3 py-2 text-sm"
                        >
                          <input
                            type="radio"
                            name={`question-${index}`}
                            value={optionCode}
                            checked={answers[index] === optionCode}
                            onChange={() => setAnswers((prev) => ({ ...prev, [index]: optionCode }))}
                          />
                          <span>{`${optionCode}. ${option}`}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 flex items-center gap-3">
              <Button type="button" onClick={handleSubmitQuiz} disabled={!canSubmit || submitAction.loading}>
                {submitAction.loading ? "Submitting..." : "Submit Quiz"}
              </Button>
              {!canSubmit ? <p className="text-xs text-accent-600">Answer all questions to submit.</p> : null}
            </div>
          </ResultBlock>

          {submitAction.error ? <Alert variant="error">{submitAction.error}</Alert> : null}

          {submission ? (
            <ResultBlock title={`Score: ${submission.correct_answers}/${submission.total_questions} (${submission.score_percentage.toFixed(1)}%)`}>
              <div className="space-y-3">
                {submission.results.map((item) => (
                  <div
                    key={item.question_index}
                    className={`rounded-lg border px-3 py-2 ${item.is_correct ? "border-success-500/30 bg-success-50" : "border-danger-500/30 bg-danger-50"}`}
                  >
                    <p className="text-sm font-semibold text-accent-800">
                      {`Q${item.question_index + 1}: ${item.is_correct ? "Correct" : "Incorrect"}`}
                    </p>
                    <p className="text-xs text-accent-700">
                      Your answer: {item.selected_option || "-"} | Correct: {item.correct_option}
                    </p>
                    <p className="mt-1 text-xs text-accent-700">{item.explanation}</p>
                  </div>
                ))}
              </div>
            </ResultBlock>
          ) : null}
        </div>
      ) : null}
    </FeatureShell>
  );
}
