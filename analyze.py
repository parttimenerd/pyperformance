"""
Program that takes multiple JSON files from pyperf
and plots it using plotly.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class BenchmarkResult:
    name: str
    mode: str
    tags: List[str]
    mean: float
    stddev: float


@dataclass
class BenchmarkResults:
    mode: str
    benchmarks: List[BenchmarkResult]

    @staticmethod
    def from_json(mode: str, json: dict) -> 'BenchmarkResults':
        benchmarks = []
        for benchmark in json['benchmarks']:
            name = benchmark['metadata']['name']
            tags = benchmark['metadata']['tags']
            values = [v for r in benchmark["runs"] if "values" in r
                      for v in r["values"]]
            mean = sum(values) / len(values)
            stddev = (sum((v - mean) ** 2 for v in values) / len(
                values)) ** 0.5
            benchmarks.append(
                BenchmarkResult(name, mode, tags, mean, stddev))
        return BenchmarkResults(mode, benchmarks)

    @staticmethod
    def from_file(path: Path) -> 'BenchmarkResults':
        with open(path) as f:
            return BenchmarkResults.from_json(
                path.stem.replace('.json', ''), json.load(f))

    def get_benchmark(self, name: str) -> BenchmarkResult:
        return next(b for b in self.benchmarks if b.name == name)


@dataclass
class BenchmarkComp:
    mode: str
    relative_mean: float
    relative_std: float


@dataclass
class BenchmarkComparison:
    name: str
    tags: List[str]
    comparisons: List[BenchmarkComp]

    @staticmethod
    def from_benchmarks(baseline: BenchmarkResult, results: List[
        BenchmarkResult]) -> 'BenchmarkComparison':
        comparisons = []
        for result in results:
            comparisons.append(BenchmarkComp(result.mode,
                                             result.mean / baseline.mean,
                                             max(result.stddev,
                                                 baseline.stddev) / min(
                                                 result.mean,
                                                 baseline.mean)))
        return BenchmarkComparison(baseline.name, baseline.tags,
                                   comparisons)

    def for_mode(self, mode: str) -> BenchmarkComp:
        return next(c for c in self.comparisons if c.mode == mode)


@dataclass
class BenchmarkComparisons:
    comparisons: List[BenchmarkComparison]

    @staticmethod
    def from_benchmarks(baseline: BenchmarkResults, comparisons: List[
        BenchmarkResults]) -> 'BenchmarkComparisons':
        return BenchmarkComparisons([
                                        BenchmarkComparison.from_benchmarks(
                                            baseline.get_benchmark(
                                                b.name),
                                            [c.get_benchmark(b.name)
                                             for c in comparisons])
                                        for b in baseline.benchmarks
                                        if b.name != "2to3"])

    def geometric_mean(self, mode: str) -> float:
        def prod(iterable):
            p = 1
            for n in iterable:
                p *= n
            return p

        return (prod(c.for_mode(mode).relative_mean for c in
                     self.comparisons)) ** (1 / len(self.comparisons))

    def plot(self):
        """
        Plot a grouped bar plot using the relative mean and relative stddev per comparison.

        Group the bars by benchmark name.
        """
        import plotly.graph_objects as go
        names = [c.name for c in self.comparisons]
        modes = [c.mode for c in self.comparisons[0].comparisons]

        fig = go.Figure(
            data=[
                go.Bar(name=m, x=names,
                       y=[c.for_mode(m).relative_mean for c in
                          self.comparisons], error_y=dict(type='data',
                                                          array=[
                                                              c.for_mode(
                                                                  m).relative_std
                                                              for c in
                                                              self.comparisons]))
                for m in modes
            ])
        # min y value is 1
        fig.update_yaxes(range=[1, 10])
        fig.add_hline(y=1, line_color="black")
        # start y axis at 1
        # make y labels larger font
        fig.update_yaxes(tickfont=dict(size=18))
        fig.update_yaxes(automargin=True)
        fig.update_layout(barmode='group')
        for m in modes:
            # line for geometric mean of each mode in the modes bar color
            fig.add_hline(y=self.geometric_mean(m),
                          line_color="black", line_dash="dash",
                          line_width=3)
            # add a y tick for the geometric mean of each mode in the modes bar color
            fig.add_annotation(x=-2, y=self.geometric_mean(m),
                               text=f"{round(self.geometric_mean(m), 1)}",
                               showarrow=False, yshift=10,
                               font=dict(size=18, color=fig.data[
                                   modes.index(m)].marker.color))
        # title y axis as "relative to baseline"
        fig.update_yaxes(title_text="relative to baseline",
                         title_font=dict(size=18))
        # title x axis as "benchmark"
        fig.update_xaxes(title_text="benchmark",
                         title_font=dict(size=18))
        # put legend inside the plot
        fig.update_layout(legend=dict(x=0.9, y=0.95),
                          legend_font=dict(size=18))
        # use simple_white theme
        fig.update_layout(template="simple_white")
        fig.show()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Plot pyperf results')
    parser.add_argument('baseline', type=str, help='baseline file')
    parser.add_argument('comparisons', type=str, nargs='+',
                        help='comparison files')
    args = parser.parse_args()
    baseline = BenchmarkResults.from_file(Path(args.baseline))
    comparisons = [BenchmarkResults.from_file(Path(c)) for c in
                   args.comparisons]
    BenchmarkComparisons.from_benchmarks(baseline, comparisons).plot()
