package de.finatix.v1

import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlin.random.Random
import kotlin.time.Duration.Companion.milliseconds

suspend fun main() {
    val limit = 100

    coroutineScope {
        IntRange(1, limit)
            .map {
                async {
                    process(it)
                }
            }
            .forEach { println(it.await()) }
    }
}

suspend fun process(i: Int): String {
    return setOf(Pair(i, ""))
        .map { check(it, 3, "Fizz") }
        .map { check(it, 5, "Buzz") }
        .map { check(it, 7, "Bazz") }
        .map { finalize(it) }
        .apply { delay(Random.nextLong(500).milliseconds) }[0]
}

fun check(input: Pair<Int, String>, divisor: Int, replacement: String): Pair<Int, String> {
    if (input.first % divisor == 0) {
        return Pair(input.first, input.second + replacement)
    }
    return input
}

fun finalize(input: Pair<Int, String>): String {
    if (input.second.isBlank()) {
        return input.first.toString()
    }
    return input.second
}
