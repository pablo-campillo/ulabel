import { create } from 'zustand'
import type { Project, AssignedImage, SubmitLabelResult } from '../types/api'

export type LabelingPhase = 'idle' | 'labeling' | 'submitted' | 'no_more_images'

interface LabelingState {
  project: Project | null
  image: AssignedImage | null
  labelCount: number
  ranking: number
  totalLabelers: number
  previousRanking: number | null
  phase: LabelingPhase

  setProject: (p: Project) => void
  setImage: (img: AssignedImage | null) => void
  setInitialStats: (count: number, ranking: number, totalLabelers: number) => void
  onLabelSubmitted: (result: SubmitLabelResult) => void
  setPhase: (phase: LabelingPhase) => void
  reset: () => void
}

export const useLabelingStore = create<LabelingState>()((set, get) => ({
  project: null,
  image: null,
  labelCount: 0,
  ranking: 0,
  totalLabelers: 0,
  previousRanking: null,
  phase: 'idle',

  setProject: (project) => set({ project }),

  setImage: (image) => set({ image }),

  setInitialStats: (labelCount, ranking, totalLabelers) =>
    set({ labelCount, ranking, totalLabelers, previousRanking: null }),

  onLabelSubmitted: (result) => {
    const currentRanking = get().ranking
    set({
      labelCount: result.labeler_count,
      previousRanking: currentRanking,
      ranking: result.ranking,
      totalLabelers: result.total_labelers,
      phase: 'submitted',
    })
  },

  setPhase: (phase) => set({ phase }),

  reset: () =>
    set({
      project: null,
      image: null,
      labelCount: 0,
      ranking: 0,
      totalLabelers: 0,
      previousRanking: null,
      phase: 'idle',
    }),
}))
