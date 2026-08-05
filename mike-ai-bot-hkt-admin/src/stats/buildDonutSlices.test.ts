import { buildDonutSlices } from './buildDonutSlices'

test('slices under 5% fold into Прочее and whole percents sum to 100', () => {
  const slices = buildDonutSlices([
    { key: 'a', label: 'A', value: 42 },
    { key: 'b', label: 'B', value: 25 },
    { key: 'c', label: 'C', value: 18 },
    { key: 'd', label: 'D', value: 10 },
    { key: 'e', label: 'E', value: 3 },
    { key: 'f', label: 'F', value: 2 },
  ])

  expect(slices.map((s) => s.label)).toEqual(['A', 'B', 'C', 'D', 'Прочее'])
  expect(slices.find((s) => s.label === 'Прочее')?.value).toBe(5)
  expect(slices.reduce((sum, s) => sum + s.percent, 0)).toBe(100)
  expect(slices.every((s) => Number.isInteger(s.percent))).toBe(true)
})

test('empty or zero-only input yields no slices', () => {
  expect(buildDonutSlices([])).toEqual([])
  expect(buildDonutSlices([{ key: 'a', label: 'A', value: 0 }])).toEqual([])
})
