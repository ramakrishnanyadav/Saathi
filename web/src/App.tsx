import { Suspense, lazy } from 'react';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { Shell } from './routes/Shell';

// Route-level code splitting with React.lazy
const Landing = lazy(() => import('./routes/Landing').then((m) => ({ default: m.Landing })));
const TodayFeature = lazy(() => import('./routes/TodayFeature').then((m) => ({ default: m.TodayFeature })));
const ThreadDetail = lazy(() => import('./routes/ThreadDetail').then((m) => ({ default: m.ThreadDetail })));
const AddFeature = lazy(() => import('./routes/AddFeature').then((m) => ({ default: m.AddFeature })));
const WeekFeature = lazy(() => import('./routes/WeekFeature').then((m) => ({ default: m.WeekFeature })));
const MoneyFeature = lazy(() => import('./routes/MoneyFeature').then((m) => ({ default: m.MoneyFeature })));
const HistoryFeature = lazy(() => import('./routes/HistoryFeature').then((m) => ({ default: m.HistoryFeature })));
const HouseFeature = lazy(() => import('./routes/HouseFeature').then((m) => ({ default: m.HouseFeature })));
const PrivacyFeature = lazy(() => import('./routes/PrivacyFeature').then((m) => ({ default: m.PrivacyFeature })));
const LabFeature = lazy(() => import('./routes/LabFeature').then((m) => ({ default: m.LabFeature })));
const NotFound = lazy(() => import('./routes/NotFound').then((m) => ({ default: m.NotFound })));

function RouteFallback() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', color: 'var(--ink-500)' }}>
      <div className="font-sora" style={{ fontSize: 14, fontWeight: 600 }}>Loading SAATH...</div>
    </div>
  );
}

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <Suspense fallback={<RouteFallback />}>
        <Landing />
      </Suspense>
    ),
  },
  {
    path: '/app',
    element: <Shell />,
    children: [
      { path: '', element: <Navigate to="/app/today" replace /> },
      {
        path: 'today',
        element: (
          <Suspense fallback={<RouteFallback />}>
            <TodayFeature />
          </Suspense>
        ),
      },
      {
        path: 'threads/:id',
        element: (
          <Suspense fallback={<RouteFallback />}>
            <ThreadDetail />
          </Suspense>
        ),
      },
      {
        path: 'add',
        element: (
          <Suspense fallback={<RouteFallback />}>
            <AddFeature />
          </Suspense>
        ),
      },
      {
        path: 'week',
        element: (
          <Suspense fallback={<RouteFallback />}>
            <WeekFeature />
          </Suspense>
        ),
      },
      {
        path: 'money',
        element: (
          <Suspense fallback={<RouteFallback />}>
            <MoneyFeature />
          </Suspense>
        ),
      },
      {
        path: 'history',
        element: (
          <Suspense fallback={<RouteFallback />}>
            <HistoryFeature />
          </Suspense>
        ),
      },
      {
        path: 'house',
        element: (
          <Suspense fallback={<RouteFallback />}>
            <HouseFeature />
          </Suspense>
        ),
      },
      {
        path: 'privacy',
        element: (
          <Suspense fallback={<RouteFallback />}>
            <PrivacyFeature />
          </Suspense>
        ),
      },
      {
        path: 'lab',
        element: (
          <Suspense fallback={<RouteFallback />}>
            <LabFeature />
          </Suspense>
        ),
      },
    ],
  },
  {
    path: '*',
    element: (
      <Suspense fallback={<RouteFallback />}>
        <NotFound />
      </Suspense>
    ),
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
