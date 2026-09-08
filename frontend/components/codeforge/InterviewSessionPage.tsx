'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArrowLeft, CheckCircle2, Circle, Send } from 'lucide-react';
import { Button, Spinner, StatCard } from './SharedComponents';
import CodeEditor from './CodeEditor';
import {
  useInterviewSession,
  useSubmitInterviewAnswer,
  useSubmitInterviewCode,
  useFinishInterview,
  useProblem,
  useSubmitSolution,
  useSubmissionPolling,
} from '@/lib/api/hooks';
import { apiErrorMessage } from '@/lib/api/client';
import type { InterviewQuestionResponse } from '@/lib/api/types';

const InterviewSessionPage: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const { data: session, isLoading } = useInterviewSession(sessionId);
  const finishMutation = useFinishInterview(sessionId);
  const [error, setError] = useState<string | null>(null);

  if (isLoading || !session) {
    return (
      <div className="flex h-full items-center justify-center bg-[#0B0F17]">
        <Spinner size={28} />
      </div>
    );
  }

  const isDone = session.status === 'completed';
  const answeredIds = new Set(session.answers.map((a) => a.question_id));

  return (
    <div className="min-h-full bg-[#0B0F17] p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <Link
          href="/interviews"
          className="flex w-fit items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-300"
        >
          <ArrowLeft size={13} /> Back to interviews
        </Link>

        <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-6">
          <div className="mb-1 flex items-center justify-between">
            <h1 className="text-xl font-bold text-white">{session.title}</h1>
            <span
              className={`text-sm font-semibold ${isDone ? 'text-emerald-400' : 'text-amber-400'}`}
            >
              {session.status.replace('_', ' ')}
            </span>
          </div>
          <p className="text-xs text-gray-500">
            {session.type.replace('_', ' ')} · {session.time_limit_minutes} minute limit
          </p>
        </div>

        {error && (
          <div className="rounded-lg border border-rose-900/50 bg-rose-950/30 px-4 py-2.5 text-sm text-rose-400">
            {error}
          </div>
        )}

        {session.feedback ? (
          <div className="space-y-4 rounded-lg border border-gray-800 bg-gray-900/60 p-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <StatCard
                label="Overall score"
                value={`${session.feedback.overall_score.toFixed(0)}%`}
                color="cyan"
              />
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-emerald-500">
                Strengths
              </p>
              <ul className="list-inside list-disc space-y-1 text-sm text-gray-300">
                {session.feedback.strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-amber-500">
                Areas to improve
              </p>
              <ul className="list-inside list-disc space-y-1 text-sm text-gray-300">
                {session.feedback.improvements.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            <div className="markdown-body text-sm text-gray-300">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {session.feedback.summary_md}
              </ReactMarkdown>
            </div>
          </div>
        ) : (
          <>
            {session.questions
              .sort((a, b) => a.order - b.order)
              .map((question) => (
                <QuestionPanel
                  key={question.id}
                  sessionId={sessionId}
                  question={question}
                  answered={answeredIds.has(question.id)}
                />
              ))}

            {!isDone && (
              <Button
                variant="success"
                onClick={() => {
                  setError(null);
                  finishMutation.mutate(undefined, {
                    onError: (err) =>
                      setError(apiErrorMessage(err, 'Could not finish the interview.')),
                  });
                }}
                disabled={finishMutation.isPending}
              >
                {finishMutation.isPending ? 'Evaluating...' : 'Finish interview & get feedback'}
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  );
};

const QuestionPanel: React.FC<{
  sessionId: string;
  question: InterviewQuestionResponse;
  answered: boolean;
}> = ({ sessionId, question, answered }) => {
  if (question.question_type === 'coding' && question.problem_id) {
    return <CodingQuestionPanel sessionId={sessionId} question={question} answered={answered} />;
  }
  return <TextQuestionPanel sessionId={sessionId} question={question} answered={answered} />;
};

const TextQuestionPanel: React.FC<{
  sessionId: string;
  question: InterviewQuestionResponse;
  answered: boolean;
}> = ({ sessionId, question, answered }) => {
  const [answerText, setAnswerText] = useState('');
  const [submitted, setSubmitted] = useState(answered);
  const mutation = useSubmitInterviewAnswer(sessionId);

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-5">
      <div className="mb-3 flex items-center gap-2">
        {submitted ? (
          <CheckCircle2 size={16} className="text-emerald-500" />
        ) : (
          <Circle size={16} className="text-gray-700" />
        )}
        <span className="text-sm font-medium text-gray-200">{question.question_text}</span>
      </div>
      <textarea
        value={answerText}
        onChange={(e) => setAnswerText(e.target.value)}
        disabled={submitted}
        rows={5}
        placeholder="Write your answer..."
        className="w-full resize-y rounded-lg border border-gray-800 bg-gray-950/60 p-3 text-sm text-gray-200 placeholder-gray-600 focus:border-cyan-700 focus:outline-none disabled:opacity-60"
      />
      {!submitted && (
        <Button
          size="sm"
          className="mt-3"
          disabled={!answerText.trim() || mutation.isPending}
          onClick={() =>
            mutation.mutate(
              { question_id: question.id, answer_text: answerText },
              { onSuccess: () => setSubmitted(true) }
            )
          }
        >
          <Send size={14} />
          Submit answer
        </Button>
      )}
    </div>
  );
};

const CodingQuestionPanel: React.FC<{
  sessionId: string;
  question: InterviewQuestionResponse;
  answered: boolean;
}> = ({ sessionId, question, answered }) => {
  const { data: problem } = useProblem(question.problem_id ?? undefined);
  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState('');
  const [submissionId, setSubmissionId] = useState<string | undefined>();
  const [linked, setLinked] = useState(answered);
  const [error, setError] = useState<string | null>(null);

  const submitSolution = useSubmitSolution(question.problem_id ?? '');
  const submitCode = useSubmitInterviewCode(sessionId);
  const { data: polled } = useSubmissionPolling(submissionId);

  useEffect(() => {
    if (!problem) return;
    const initial = problem.supported_languages.includes('python')
      ? 'python'
      : problem.supported_languages[0];
    setLanguage(initial);
    setCode(problem.starter_code[initial] ?? '');
  }, [problem?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (polled?.completed_at && submissionId && !linked) {
      submitCode.mutate(
        { question_id: question.id, submission_id: submissionId },
        {
          onSuccess: () => setLinked(true),
          onError: (err) =>
            setError(
              apiErrorMessage(err, 'Could not record this submission against the interview.')
            ),
        }
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [polled?.completed_at, submissionId, linked]);

  if (!problem) {
    return (
      <div className="flex h-32 items-center justify-center rounded-lg border border-gray-800 bg-gray-900/60">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-5">
      <div className="mb-3 flex items-center gap-2">
        {linked ? (
          <CheckCircle2 size={16} className="text-emerald-500" />
        ) : (
          <Circle size={16} className="text-gray-700" />
        )}
        <span className="text-sm font-medium text-gray-200">{question.question_text}</span>
      </div>
      <CodeEditor
        value={code}
        onChange={setCode}
        language={language}
        onLanguageChange={(next) => {
          setLanguage(next);
          setCode(problem.starter_code[next] ?? '');
        }}
        availableLanguages={problem.supported_languages}
        height="300px"
      />
      {polled && (
        <p className="mt-3 text-xs text-gray-500">
          Submission status:{' '}
          <span className="font-semibold text-gray-300">{polled.status.replace('_', ' ')}</span>
          {!polled.completed_at && ' — judging...'}
        </p>
      )}
      {error && <p className="mt-2 text-xs text-rose-400">{error}</p>}
      {!linked && (
        <Button
          size="sm"
          className="mt-3"
          disabled={submitSolution.isPending || !!submissionId}
          onClick={() => {
            setError(null);
            submitSolution.mutate(
              { language, source_code: code },
              {
                onSuccess: (data) => setSubmissionId(data.id),
                onError: (err) => setError(apiErrorMessage(err, 'Could not submit your solution.')),
              }
            );
          }}
        >
          <Send size={14} />
          {submissionId ? 'Waiting for judge...' : 'Submit & link to interview'}
        </Button>
      )}
    </div>
  );
};

export default InterviewSessionPage;
