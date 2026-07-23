"""Module for CIViC variant normalization"""

import re
from dataclasses import dataclass
from enum import StrEnum
from civicpy import civic as civicpy
from gene.query import QueryHandler as GeneQueryHandler
from variation.query import QueryHandler
from ga4gh.vrs.models import Allele
from ga4gh.vrs.utils.hgvs_tools import HgvsTools
from typing import Any, Protocol, TypeAlias
from utils import NotSupportedVariantCategory  # noqa: E402
from hgvs.assemblymapper import AssemblyMapper

CDNA_CHANGE_PATTERN = re.compile(r"^(?!.*c\..*c\.).*?(?:\((c\.[^)]+)\)|(c\.\S+))$")


class VariantQueryType(StrEnum):
    """Define variant query types"""

    CDNA_GENOMIC = (
        "cdna_genomic"  # these are civic variants that have 'c.' in their name
    )
    PROTEIN = "protein"


class CsvWriter(Protocol):
    """Protocol for CSV writer objects."""

    def writerow(self, row: list[Any]) -> Any:
        """Write one CSV row."""


CountTotals: TypeAlias = dict[VariantQueryType, dict[str, int]]


@dataclass
class NormalizationContext:
    """Resources used while normalizing CIViC variants.

    :param query_handler: Handler used to normalize variation queries.
    :param gene_query_handler: Handler used to normalize gene symbols.
    :param hgvs_tools: Extra tools for working with hgvs exprsesions.
    :param am: HGVS assembly mapper.
    :param category_counts: Counts grouped by unsupported variant category.
    :param can_normalize_totals: Successful normalization counts.
    :param unable_to_normalize_totals: Failed normalization counts.
    :param exception_totals: Exception counts.
    :param able_writer: Writer for successfully normalized variants.
    :param unable_writer: Writer for variants that could not be normalized.
    :param not_supported_writer: Writer for unsupported variants.
    """

    query_handler: QueryHandler
    gene_query_handler: GeneQueryHandler
    hgvs_tools: HgvsTools
    am: AssemblyMapper
    category_counts: dict[str, int]
    can_normalize_totals: CountTotals
    unable_to_normalize_totals: CountTotals
    exception_totals: CountTotals
    able_writer: CsvWriter
    unable_writer: CsvWriter
    not_supported_writer: CsvWriter


@dataclass(frozen=True)
class VariantNormalizationInput:
    """Input values for normalizing one CIViC variant.

    :param variant: CIViC variant being processed.
    :param query: Query submitted to the variation normalizer.
    :param variant_name: Parsed CIViC variant name.
    :param query_type: Type of variation query
    :param gene_name: Associated gene symbol, if available.
    :param civic_variant_types: Semicolon-delimited CIViC variant types.
    :param is_accepted: Whether the variant has accepted evidence.
    :param accepted_key: Count key for the variant review status.
    """

    variant: civicpy.Variant
    query: str
    variant_name: str
    query_type: VariantQueryType
    gene_name: str | None
    civic_variant_types: str
    is_accepted: bool
    accepted_key: str


def total_counts() -> dict:
    """Return initial total counts for genomic and protein variants"""
    return {
        VariantQueryType.PROTEIN: {"accepted": 0, "submitted": 0, "count": 0},
        VariantQueryType.CDNA_GENOMIC: {"accepted": 0, "submitted": 0, "count": 0},
    }


def is_accepted_variant(v: civicpy.Variant) -> bool:
    """Return whether or not a variant (MPs) has at least one EID in an accepted status.

    :param v: CIViC variant
    :return: `True` if considered accepted variant. `False` otherwise.
    """
    for mp in v.molecular_profiles:
        for ev in mp.evidence_items:
            if ev.status == "accepted":
                return True
    return False


def get_variant_name_and_type(variant: civicpy.Variant) -> tuple[str, VariantQueryType]:
    """Get transformed variant name and type

    :param variant: CIViC variant record
    :return: Tuple containing variant name to use in variation-normalizer and the civic
        variant type
    """
    v_name = variant.name.strip()

    if "c." in variant.name:
        v_q_type = VariantQueryType.CDNA_GENOMIC
    else:
        v_q_type = VariantQueryType.PROTEIN

    return v_name, v_q_type


def get_gene_cdna_query(gene: str | None, variant_name: str) -> str | None:
    """Attempt to get gene cDNA only change from name

    :param gene: Gene name
    :param variant_name: Variant name
    """
    if not gene:
        return

    if len(variant_name.split(" ")) > 2:
        # this may be something like 'Deletion AND I151S(c.452T>G)' which we dont support
        return

    match = CDNA_CHANGE_PATTERN.fullmatch(variant_name)
    cdna_change = (match.group(1) or match.group(2)) if match else None

    if not cdna_change:
        return

    return f"{gene} {cdna_change}"


async def map_transcript_to_genomic(
    query_handler: QueryHandler,
    hgvs_tools: HgvsTools,
    am: AssemblyMapper,
    transcript_vo: Allele,
) -> dict:
    """Translate transcript VRS Allele to genomic VRS Allele

    Will attempt to align to GRCh38

    :param query_handler: Handler used to normalize variation queries.
    :param hgvs_tools: Extra tools for working with hgvs exprsesions.
    :param am: HGVS assembly mapper.
    :param transcript_vo: Transcript VRS Allele
    :return: Response containing mapped genomic vrs_id (if successful) and errors
        (if unsuccessful)
    """
    try:
        cdna_hgvs_expressions = query_handler.vrs_python_tlr.translate_to(
            transcript_vo, fmt="hgvs"
        )
    except Exception as e:
        return {"vrs_id": None, "error": str(e)}

    for cdna_hgvs_expr in cdna_hgvs_expressions:
        try:
            var_c = hgvs_tools.parser.parse_hgvs_variant(cdna_hgvs_expr)
            var_g = am.c_to_g(var_c)
            g_variation_norm_resp = await query_handler.normalize_handler.normalize(
                str(var_g)
            )
        except Exception:
            continue
        else:
            if genomic_vo := g_variation_norm_resp.variation:
                return {"vrs_id": genomic_vo.id, "error": None}

    return {
        "vrs_id": None,
        "error": "Unable to derive genomic VRS Allele from cDNA VRS Allele",
    }


def get_not_supported_categories(
    gene_query_handler: GeneQueryHandler,
    v_name: str,
    variant: civicpy.Variant,
    not_supported: dict,
) -> set[NotSupportedVariantCategory]:
    """Get not supported categories for a CIViC variant.

    :param gene_query_handler: Handler used to normalize gene symbols.
    :param v_name: Variant query to provide to the variation-normalizer
    :param variant: CIViC variant record
    :param not_supported: Not supported items
    :return: Set of associated NotSupportedVariantCategory for a variant. If supported,
        empty set will be returned
    """
    v_name_lower = v_name.lower()
    categories = set()

    variant_subtype = variant.subtype
    if variant_subtype == "factor_variant":
        if variant.factor.name == "C19MC":
            categories.add(NotSupportedVariantCategory.REGION_DEFINED)
        else:
            categories.add(NotSupportedVariantCategory.GENOME_FEATURE)
    elif variant_subtype == "fusion_variant":
        categories.add(NotSupportedVariantCategory.FUSION)
    elif v_name_lower in {"loss", "deletion"}:
        categories.add(NotSupportedVariantCategory.GENE_FUNCTION)
    elif any(
        (
            v_name_lower in {"mutation", "mutations", "snp"},
            hasattr(variant, "gene")
            and v_name_lower == f"{variant.gene.name.lower()} mutation",
        )
    ):
        categories.add(NotSupportedVariantCategory.REGION_DEFINED)
    else:
        if v_name_lower.endswith("deletion and mutation"):
            v_name_split = v_name.split()
            if len(v_name_split) == 4:
                if gene_query_handler.normalize(v_name_split[0]).match_type > 0:
                    categories.add(NotSupportedVariantCategory.REGION_DEFINED)

        if re.match(r"intron\s\d+\smutation", v_name_lower):  # ex: Intron 6 Mutation
            categories.add(NotSupportedVariantCategory.REGION_DEFINED)

        if any(
            (
                "exon" in v_name_lower,
                re.match(r"t\(.*\)\(.*\)", v_name_lower),  # ex: t(1;3)(p36.3;p25)
                re.match(r".*ins$", v_name_lower),  # ex: P780INS, L78_Q79ins
                re.match(
                    r"\w+_?\w+>\w+", v_name_lower
                ),  # ex: 56_61QKQKVG>R, E746_T751>I, N771>GY
                re.match(r"\d+kb\sdeletion", v_name_lower),  # ex: 10kb Deletion
                re.match(
                    r"partial\sdeletion\sof\s\d+(.\d+)?\skb", v_name_lower
                ),  # ex: Partial deletion of 0.7 Kb
                re.match(
                    r"\d+(p|q)\d+(.\d+)?-\d+(.\d+)?\s\d+mb del", v_name_lower
                ),  # ex: 3p26.3-25.3 11Mb del
            )
        ):
            categories.add(NotSupportedVariantCategory.REARRANGEMENT)

        if any(
            (
                re.match(r"^rs\d+", v_name_lower),  # ex: RS11623866
                re.match(r"class\s\d+\smutation", v_name_lower),  # ex: Class 3 Mutation
            )
        ):
            categories.add(NotSupportedVariantCategory.OTHER)

        if re.match(r"cd\d+v?\d+", v_name_lower):  # cd44, cd44v6
            categories.add(NotSupportedVariantCategory.EXPRESSION)

        if any(
            (
                re.match(r"\w+\d+$", v_name_lower),  # ex: V600
                re.match(r"\w+\d+\w+\/\w+$", v_name_lower),  # ex: S893A/T
                re.match(
                    r"[a-z]+\d+[a-z]+\sand\s[a-z]+\d+[a-z|*]+", v_name_lower
                ),  # ex: E2014K and E2419K, R849W and R1108*
                re.match(r"[a-z]+\d+\s&\s[a-z]+\d+", v_name_lower),  # ex: D835 & I836
                re.match(
                    r"[a-z]+\d+[a-z]+\sor\s[a-z]+\d+[a-z]+", v_name_lower
                ),  # ex: H1047L or H1047R
                re.match(r"\w+\d+\smutations", v_name_lower),  # ex: E1813 mutations
                re.match(
                    r"\d+\s\((c|a|g|t)+-(c|a|g|t)+\)", v_name_lower
                ),  # ex: 235 (CAG-TAG)
                re.match(r"del\s\d+-\d+", v_name_lower),  # ex: DEL 485-490
            )
        ):
            categories.add(NotSupportedVariantCategory.SEQUENCE)

        if re.match(
            r"grch3(7|8)\/hg\d+\s\w+.?\d*\(chr\w+:\d+-\d+\)x\d+", v_name_lower
        ):  # ex: GRCh37/hg19 11q14.3(chr11:88960991-88961138)x160
            categories.add(NotSupportedVariantCategory.COPY_NUMBER)

        if re.match(r"\w+[^fs]\*\d+$", v_name_lower):  # ex: UGT1A1*28
            categories.add(NotSupportedVariantCategory.GENOTYPE_AND_HAPLOTYPE)

        if re.match(r"^\*02:(?:0[1-3]|06)p$", v_name_lower):
            categories.add(NotSupportedVariantCategory.GENOTYPE_AND_HAPLOTYPE)

        for k, v in not_supported.items():
            if {x for x in v if x in v_name_lower}:
                categories.add(k)

    if len(categories) > 1:
        # Those with multiple categories will be classified as other
        categories = {NotSupportedVariantCategory.OTHER}

    return categories


def increment_total(
    totals: dict, v_q_type: VariantQueryType, accepted_key: str
) -> None:
    """Increment totals dictionary in-place

    :param totals: Totals dictionary
    :param v_q_type: Variant query type
    :param accepted_key: Accepted key
    """
    totals[v_q_type]["count"] += 1
    totals[v_q_type][accepted_key] += 1


def get_gene_query_category(
    variant_name: str,
    gene_query_handler: GeneQueryHandler,
) -> NotSupportedVariantCategory | None:
    """Determine whether a failed protein query contains only gene symbols.

    A single recognized gene is categorized as `NotSupportedVariantCategory.OTHER`.
    Multiple recognized genes separated by hyphens are categorized as
    `NotSupportedVariantCategory.FUSION`.

    :param variant_name: Protein variant name that failed normalization.
    :param gene_query_handler: Handler used to normalize gene symbols.
    :return: Unsupported category when all tokens are recognized genes.
        Otherwise, `None`.
    """
    genes = variant_name.split("-")

    if not all(gene_query_handler.normalize(gene).match_type != 0 for gene in genes):
        return None

    if len(genes) > 1:
        return NotSupportedVariantCategory.FUSION

    return NotSupportedVariantCategory.OTHER


def write_not_supported(
    item: VariantNormalizationInput,
    category: NotSupportedVariantCategory,
    context: NormalizationContext,
) -> None:
    """Record a variant belonging to an unsupported category.

    :param item: Variant-specific normalization input.
    :param category: Unsupported variant category.
    :param context: Shared counters and CSV writers.
    """
    context.category_counts[category.name] += 1
    context.not_supported_writer.writerow(
        [
            item.variant.id,
            item.gene_name,
            item.variant.name,
            item.civic_variant_types,
            category,
            item.is_accepted,
        ]
    )


def write_normalization_success(
    item: VariantNormalizationInput,
    vrs_id: str,
    method: str,
    context: NormalizationContext,
) -> None:
    """Record a successfully normalized variant.

    :param item: Variant-specific normalization input.
    :param vrs_id: Computed VRS identifier.
    :param method: Method used to obtain the VRS identifier.
    :param context: Shared counters and CSV writers.
    """
    increment_total(
        context.can_normalize_totals,
        item.query_type,
        item.accepted_key,
    )
    context.able_writer.writerow(
        [
            item.variant.id,
            item.query,
            item.query_type,
            item.is_accepted,
            item.civic_variant_types,
            vrs_id,
            method,
        ]
    )


def write_normalization_failure(
    item: VariantNormalizationInput,
    *,
    raised_exception: bool,
    reason: str | list[str],
    warnings: list[str] | None,
    context: NormalizationContext,
) -> None:
    """Record a variant that could not be normalized.

    :param item: Variant-specific normalization input.
    :param raised_exception: Whether the failure represents an exception.
    :param reason: Description of the normalization failure.
    :param warnings: Normalizer warnings, when available.
    :param context: Shared counters and CSV writers.
    """
    context.unable_writer.writerow(
        [
            item.variant.id,
            item.query,
            item.query_type,
            item.is_accepted,
            item.civic_variant_types,
            raised_exception,
            reason,
            warnings,
        ]
    )


def write_expected_failure(
    item: VariantNormalizationInput,
    *,
    reason: str,
    warnings: list[str],
    context: NormalizationContext,
) -> None:
    """Record an expected normalization failure.

    :param item: Variant-specific normalization input.
    :param reason: Description of the failure.
    :param warnings: Normalizer warnings.
    :param context: Shared counters and CSV writers.
    """
    write_normalization_failure(
        item,
        raised_exception=False,
        reason=reason,
        warnings=warnings,
        context=context,
    )
    increment_total(
        context.unable_to_normalize_totals,
        item.query_type,
        item.accepted_key,
    )


def write_exception(
    item: VariantNormalizationInput,
    error: str,
    context: NormalizationContext,
) -> None:
    """Record a normalization or mapping exception.

    :param item: Variant-specific normalization input.
    :param error: Exception or mapping error message.
    :param context: Shared counters and CSV writers.
    """
    write_normalization_failure(
        item,
        raised_exception=True,
        reason=sorted([error]),
        warnings=None,
        context=context,
    )
    increment_total(
        context.exception_totals,
        item.query_type,
        item.accepted_key,
    )


async def normalize_cdna_variant(
    item: VariantNormalizationInput,
    variation: Any,
    context: NormalizationContext,
    normalized_as_is: bool = True,
) -> None:
    """Map a normalized transcript allele to genomic coordinates.

    :param item: Variant-specific normalization input.
    :param variation: Variation returned by the normalizer.
    :param context: Shared handlers, counters, and CSV writers.
    :param normalized_as_is: Whether or not civic variant name normalized as is,
        or if modifications needed to be made
    """
    if not isinstance(variation, Allele):
        write_expected_failure(
            item,
            reason="cdna VRS variation is not a VRS Allele",
            warnings=[],
            context=context,
        )
        return

    genomic_response = await map_transcript_to_genomic(
        context.query_handler, context.hgvs_tools, context.am, variation
    )
    vrs_id = genomic_response["vrs_id"]

    if not vrs_id:
        write_exception(
            item,
            genomic_response["error"],
            context,
        )
        return

    if normalized_as_is:
        method = "normalize"
    else:
        method = "normalize_cdna_change_only"

    write_normalization_success(
        item,
        vrs_id,
        method,
        context,
    )


async def normalize_variant(
    item: VariantNormalizationInput,
    context: NormalizationContext,
) -> None:
    """Normalize one CIViC variant and record its outcome.

    :param item: Variant-specific normalization input.
    :param context: Shared handlers, counters, and CSV writers.
    """
    try:
        response = await context.query_handler.normalize_handler.normalize(item.query)
        variation = response.variation
        normalized_as_is = True

        if item.query_type == VariantQueryType.CDNA_GENOMIC and not variation:
            # If cDNA, let's try to normalize just on the gene and cDNA change
            # Sometimes the normalizer will fail if it doesn't recognize a protein token.
            # For example, 'VHL *214C (c.641_642insC)' will fail in the normalizer.
            # Second pass will attempt 'VHL (c.641_642insC)' which should succeed.

            cdna_only_query = get_gene_cdna_query(item.gene_name, item.variant_name)

            if cdna_only_query and (cdna_only_query != item.query):
                cdna_only_response = (
                    await context.query_handler.normalize_handler.normalize(
                        cdna_only_query
                    )
                )
                variation = cdna_only_response.variation
                normalized_as_is = False

        if not variation:
            category = None

            if (
                item.query_type == VariantQueryType.PROTEIN
                and len(item.variant_name.split()) == 1
            ):
                # Determine if fusion or gene name (which actually aren't supported)
                category = get_gene_query_category(
                    item.variant_name,
                    context.gene_query_handler,
                )

            if category is not None:
                write_not_supported(item, category, context)
                return

            write_expected_failure(
                item,
                reason="unable to normalize",
                warnings=sorted(response.warnings or []),
                context=context,
            )
            return

        if item.query_type == VariantQueryType.CDNA_GENOMIC:
            await normalize_cdna_variant(item, variation, context, normalized_as_is)
            return

        write_normalization_success(
            item,
            variation.id,
            "normalize",
            context,
        )

    except Exception as error:
        write_exception(item, str(error), context)
